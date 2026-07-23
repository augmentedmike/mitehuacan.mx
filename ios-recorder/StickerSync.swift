import Foundation

/// Pushes sticker placements to the admin endpoint on production (Bearer-gated,
/// same admin account as combi lines and sponsors). The server upserts the
/// `stickers` row: with lat/lon it's `placement = fijo`, without it's `combi`.
enum StickerSync {
    enum SyncError: LocalizedError {
        case badResponse, unauthorized
        var errorDescription: String? {
            switch self {
            case .badResponse:  return "No se pudo conectar con el servidor"
            case .unauthorized: return "Sesión inválida — vuelve a desbloquear"
            }
        }
    }

    static var endpoint: URL { URL(string: "\(AdminAuth.base)/api/admin/stickers")! }

    /// POST one placement. Sends lat/lon only when present — the server reads their
    /// absence as "on something that moves".
    static func push(_ p: StickerPlacement, token: String) async throws {
        var req = URLRequest(url: endpoint)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.timeoutInterval = 15
        var body: [String: Any] = ["id": p.code]
        if let lat = p.lat, let lon = p.lon { body["lat"] = lat; body["lon"] = lon }
        let route = p.routeId.trimmingCharacters(in: .whitespaces)
        if !route.isEmpty { body["route_id"] = route }
        let unit = p.unitDesc.trimmingCharacters(in: .whitespaces)
        if !unit.isEmpty { body["unit_desc"] = unit }
        let notes = p.notes.trimmingCharacters(in: .whitespaces)
        if !notes.isEmpty { body["notes"] = notes }
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (_, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard code == 200 else { throw code == 401 ? SyncError.unauthorized : SyncError.badResponse }
    }
}
