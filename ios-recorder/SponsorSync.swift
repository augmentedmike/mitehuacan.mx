import Foundation

/// Talks to the admin sponsors endpoint on production. Both read and write are gated
/// by the admin bearer token (same account as combi lines). Mirrors `RouteSync`:
/// `fetchLive` reads every sponsor + its locations; `push` upserts one sponsor and
/// full-replaces its locations.
enum SponsorSync {
    enum SyncError: LocalizedError {
        case badResponse, parse, unauthorized
        var errorDescription: String? {
            switch self {
            case .badResponse: return "No se pudo conectar con el servidor"
            case .parse:       return "No se pudo leer el formato de patrocinadores"
            case .unauthorized: return "Sesión inválida — vuelve a desbloquear"
            }
        }
    }

    static var endpoint: URL { URL(string: "\(AdminAuth.base)/api/admin/sponsors")! }

    /// GET all sponsors (authed) as local `Sponsor` values (serverId + logo decoded).
    static func fetchLive(token: String) async throws -> [Sponsor] {
        var req = URLRequest(url: endpoint)
        req.cachePolicy = .reloadIgnoringLocalCacheData
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.timeoutInterval = 15
        let (data, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard code != 401 else { throw SyncError.unauthorized }
        guard code == 200 else { throw SyncError.badResponse }
        guard let wire = try? JSONDecoder().decode(Wire.self, from: data) else { throw SyncError.parse }
        return wire.sponsors.map { $0.toSponsor() }
    }

    /// POST one sponsor + its locations (+ logo as a data URL). The server
    /// full-replaces this sponsor's locations. Throws on non-200; caller marks synced.
    static func push(_ s: Sponsor, token: String) async throws {
        var req = URLRequest(url: endpoint)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.timeoutInterval = 20
        var body: [String: Any] = [
            "slug": s.slug,
            "name": s.name,
            "contact_name": s.contactName,
            "contact_email": s.contactEmail,
            "phone": s.phone,
            "tier": s.tier,
            "notes": s.notes,
            "active": s.active ? 1 : 0,
            "locations": s.locations.map { loc -> [String: Any] in
                ["label": loc.label, "lat": loc.lat, "lon": loc.lon, "active": loc.active ? 1 : 0]
            },
        ]
        if let d = s.logoData { body["logo"] = "data:image/png;base64,\(d.base64EncodedString())" }
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (_, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard code == 200 else { throw code == 401 ? SyncError.unauthorized : SyncError.badResponse }
    }

    // MARK: - wire format

    struct Wire: Decodable { let sponsors: [WSponsor] }

    struct WSponsor: Decodable {
        let slug: String, name: String
        let contact_name: String?, contact_email: String?, phone: String?
        let tier: String?, notes: String?, active: Int?, logo: String?
        let locations: [WLoc]?

        func toSponsor() -> Sponsor {
            var s = Sponsor()
            s.slug = slug
            s.name = name
            s.contactName = contact_name ?? ""
            s.contactEmail = contact_email ?? ""
            s.phone = phone ?? ""
            s.tier = tier ?? "barter"
            s.notes = notes ?? ""
            s.active = (active ?? 1) != 0
            s.logoData = Self.decodeLogo(logo)
            s.locations = (locations ?? []).map { w in
                var l = SponsorLocation(lat: w.lat, lon: w.lon)
                l.serverId = w.id
                l.label = w.label ?? ""
                l.active = (w.active ?? 1) != 0
                return l
            }
            return s
        }

        static func decodeLogo(_ s: String?) -> Data? {
            guard let s, let mark = s.range(of: "base64,") else { return nil }
            return Data(base64Encoded: String(s[mark.upperBound...]))
        }
    }

    struct WLoc: Decodable {
        let id: Int?; let label: String?; let lat: Double; let lon: Double; let active: Int?
    }
}
