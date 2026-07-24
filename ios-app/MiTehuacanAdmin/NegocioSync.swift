import Foundation

/// Talks to the admin business-review endpoint on production. Bearer-token gated
/// (the admin PIN), like `SponsorSync`. `fetchPending` reads the review queue;
/// `review` approves (stays live) or rejects (goes dark) one listing.
enum NegocioSync {
    enum SyncError: LocalizedError {
        case badResponse, parse, unauthorized
        var errorDescription: String? {
            switch self {
            case .badResponse:  return "No se pudo conectar con el servidor"
            case .parse:        return "No se pudieron leer los negocios"
            case .unauthorized: return "Sesión inválida — vuelve a desbloquear"
            }
        }
    }

    static var endpoint: URL { URL(string: "\(AdminAuth.base)/api/admin/negocios")! }

    /// GET the listings awaiting review (authed).
    static func fetchPending(token: String) async throws -> [Negocio] {
        var req = URLRequest(url: endpoint)
        req.cachePolicy = .reloadIgnoringLocalCacheData
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.timeoutInterval = 15
        let (data, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard code != 401 else { throw SyncError.unauthorized }
        guard code == 200 else { throw SyncError.badResponse }
        guard let wire = try? JSONDecoder().decode(Wire.self, from: data) else { throw SyncError.parse }
        return wire.pending
    }

    /// action = "approve" (keep live) | "reject" (hide). Both clear it from the queue.
    static func review(id: Int, action: String, token: String) async throws {
        var req = URLRequest(url: endpoint)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.timeoutInterval = 15
        req.httpBody = try JSONSerialization.data(withJSONObject: ["id": id, "action": action])
        let (_, resp) = try await URLSession.shared.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard code == 200 else { throw code == 401 ? SyncError.unauthorized : SyncError.badResponse }
    }

    struct Wire: Decodable { let pending: [Negocio] }
}
