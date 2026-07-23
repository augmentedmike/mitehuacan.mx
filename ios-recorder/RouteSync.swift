import Foundation

/// Loads the LIVE published routes from mitehuacan.mx/routes.js and converts each
/// GeoJSON feature into a Route the app can view, edit, prune, and annotate.
/// routes.js is `const ROUTES = { FeatureCollection };` — we slice out the JSON
/// object and decode it. Each MultiLineString part becomes one segment (so the
/// existing snip/join/prune tools work on real routes).
enum RouteSync {
    static let liveURL = URL(string: "https://mitehuacan.mx/routes.js")!

    enum SyncError: LocalizedError {
        case badResponse, parse, unauthorized
        var errorDescription: String? {
            switch self {
            case .badResponse: return "No se pudo conectar con el servidor"
            case .parse: return "No se pudo leer el formato de rutas"
            case .unauthorized: return "Sesión inválida — vuelve a desbloquear"
            }
        }
    }

    /// The routes shipped INSIDE the app (routes.seed.json) — so the app is
    /// preloaded with every route on first launch, offline, with no network.
    static func loadBundled() -> [Route] {
        guard let url = Bundle.main.url(forResource: "routes.seed", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let text = String(data: data, encoding: .utf8),
              let routes = try? parse(text) else { return [] }
        return routes
    }

    /// Push one route's metadata + per-day schedule to production (Phase 1).
    /// Requires the admin token (Keychain). Geometry publishing is Phase 2.
    static func pushLine(_ r: Route, token: String) async throws {
        var req = URLRequest(url: URL(string: "\(AdminAuth.base)/api/admin/lineas")!)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.timeoutInterval = 15
        let s = r.schedule
        var body: [String: Any] = [
            "slug": r.serverId ?? r.lineName,
            "name": r.name,
            "notes": r.notes,
            "headway_min": s.weekday.intervalMin,
            "sat_headway": s.saturday.intervalMin,
            "sun_headway": s.sunday.intervalMin,
        ]
        if let fare = r.fare { body["fare_mxn"] = fare }
        func put(_ key: String, _ v: String) {
            let t = v.trimmingCharacters(in: .whitespaces)
            if !t.isEmpty { body[key] = t }
        }
        put("first_run", s.weekday.first); put("last_run", s.weekday.last)
        put("sat_first", s.saturday.first); put("sat_last", s.saturday.last)
        put("sun_first", s.sunday.first); put("sun_last", s.sunday.last)
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (_, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard code == 200 else {
            throw code == 401 ? SyncError.unauthorized : SyncError.badResponse
        }
    }

    static func fetchLive() async throws -> [Route] {
        var req = URLRequest(url: liveURL)
        req.cachePolicy = .reloadIgnoringLocalCacheData
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, http.statusCode == 200,
              let text = String(data: data, encoding: .utf8) else { throw SyncError.badResponse }
        return try parse(text)
    }

    static func parse(_ text: String) throws -> [Route] {
        guard let s = text.firstIndex(of: "{"), let e = text.lastIndex(of: "}"), s < e,
              let json = String(text[s...e]).data(using: .utf8) else { throw SyncError.parse }
        let fc = try JSONDecoder().decode(FeatureCollection.self, from: json)
        return fc.features.map { $0.toRoute() }.filter { !$0.segments.isEmpty }
    }

    // MARK: - minimal GeoJSON

    struct FeatureCollection: Decodable { let features: [Feature] }

    struct Feature: Decodable {
        let properties: Props
        let geometry: Geometry

        func toRoute() -> Route {
            let now = Date()
            let segs: [[TrackPoint]] = geometry.lines.compactMap { line in
                let pts = line.compactMap { c -> TrackPoint? in
                    c.count >= 2 ? TrackPoint(lat: c[1], lon: c[0], ts: now, acc: 5, speed: -1) : nil
                }
                return pts.count > 1 ? pts : nil
            }
            let places = (properties.places ?? "")
                .split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
            var notes: [String] = []
            if let a = properties.alias, !a.isEmpty { notes.append(a) }
            if let t = properties.terminal, !t.isEmpty { notes.append("Terminal: \(t)") }
            if let h = properties.hours, !h.isEmpty { notes.append("Horario: \(h)") }
            if let p = properties.phone, !p.isEmpty { notes.append("Tel: \(p)") }

            var r = Route()
            r.serverId = properties.id
            r.color = properties.color
            r.kind = properties.kind
            r.name = properties.name ?? properties.id ?? "Ruta"
            r.lineName = properties.id ?? ""
            r.origin = places.first ?? ""
            r.destination = places.count > 1 ? places.last! : ""
            r.notes = notes.joined(separator: " · ")
            r.segments = segs
            return r
        }
    }

    struct Props: Decodable {
        let id: String?, name: String?, alias: String?, kind: String?
        let color: String?, places: String?, terminal: String?, hours: String?, phone: String?
        enum K: String, CodingKey { case id, name, alias, kind, color, places, terminal, hours, phone }
        init(from dec: Decoder) throws {
            let c = try dec.container(keyedBy: K.self)
            // properties vary in type across routes (places is sometimes a string,
            // sometimes an array). Decode each tolerantly: string, or array joined,
            // else nil — one odd field must never fail the whole parse.
            func str(_ k: K) -> String? {
                if let s = try? c.decode(String.self, forKey: k) { return s }
                if let a = try? c.decode([String].self, forKey: k) { return a.joined(separator: ", ") }
                return nil
            }
            id = str(.id); name = str(.name); alias = str(.alias); kind = str(.kind)
            color = str(.color); places = str(.places); terminal = str(.terminal)
            hours = str(.hours); phone = str(.phone)
        }
    }

    /// Accepts MultiLineString ([[[lon,lat]]]) or LineString ([[lon,lat]]).
    struct Geometry: Decodable {
        let lines: [[[Double]]]
        enum K: String, CodingKey { case type, coordinates }
        init(from dec: Decoder) throws {
            let c = try dec.container(keyedBy: K.self)
            switch try c.decode(String.self, forKey: .type) {
            case "MultiLineString": lines = try c.decode([[[Double]]].self, forKey: .coordinates)
            case "LineString":      lines = [try c.decode([[Double]].self, forKey: .coordinates)]
            default:                lines = []
            }
        }
    }
}
