import Foundation
import Combine

/// The live review queue. Unlike sponsors/routes it keeps no local copy — it mirrors
/// the server: `load` fetches the pending listings; `review` approves or rejects one
/// and drops it from the list on success (both actions leave the queue).
@MainActor
final class NegocioStore: ObservableObject {
    @Published var pending: [Negocio] = []
    @Published var loading = false
    @Published var error = ""

    var count: Int { pending.count }
    @Published var saving = false

    /// Admin adds a business by hand. It publishes live and pre-approved, so it does
    /// NOT enter the review queue. Returns an error string (nil on success).
    func create(_ draft: NegocioDraft, token: String) async -> String? {
        saving = true; defer { saving = false }
        do {
            _ = try await NegocioSync.create(draft, token: token)
            return nil
        } catch {
            if case NegocioSync.SyncError.unauthorized = error { return "unauthorized" }
            return error.localizedDescription
        }
    }

    func load(token: String) async {
        loading = true; error = ""
        defer { loading = false }
        do { pending = try await NegocioSync.fetchPending(token: token) }
        catch { self.error = error.localizedDescription }
    }

    /// action = "approve" (stays live) | "reject" (goes dark). Removes it from the
    /// queue on success. Returns whether the session went stale (caller re-locks).
    @discardableResult
    func review(_ n: Negocio, action: String, token: String) async -> Bool {
        do {
            try await NegocioSync.review(id: n.id, action: action, token: token)
            pending.removeAll { $0.id == n.id }
            return false
        } catch {
            self.error = error.localizedDescription
            if case NegocioSync.SyncError.unauthorized = error { return true }
            return false
        }
    }
}
