import Foundation
import Combine

/// Local persistence for sponsors (JSON in the app's Documents dir) plus the same
/// reconcile pattern as routes: local edits are flagged `pendingSync` and pushed to
/// production on demand. Reads/writes to prod are gated by the admin token; entering
/// data locally never is.
final class SponsorStore: ObservableObject {
    @Published var sponsors: [Sponsor] = []

    private var url: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("sponsors.json")
    }

    init() { load() }

    /// Decode off the main thread so it never blocks app launch; publish on main.
    func load() {
        let u = url
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let data = try? Data(contentsOf: u),
                  let s = try? JSONDecoder().decode([Sponsor].self, from: data) else { return }
            DispatchQueue.main.async { self?.sponsors = s }
        }
    }
    func save() {
        if let data = try? JSONEncoder().encode(sponsors) { try? data.write(to: url) }
    }

    var pendingCount: Int { sponsors.filter { $0.pendingSync }.count }
    func markSynced(_ id: Sponsor.ID) {
        if let i = sponsors.firstIndex(where: { $0.id == id }) { sponsors[i].pendingSync = false; save() }
    }

    func add(_ s: Sponsor) { var x = s; x.pendingSync = true; sponsors.insert(x, at: 0); save() }
    func update(_ s: Sponsor) {
        if let i = sponsors.firstIndex(where: { $0.id == s.id }) {
            sponsors[i] = s; sponsors[i].pendingSync = true; save()
        }
    }
    func delete(_ s: Sponsor) { sponsors.removeAll { $0.id == s.id }; save() }

    /// Merge live sponsors by slug: add any we don't already have locally, so a
    /// re-sync never clobbers local edits or freshly entered sponsors. Returns #added.
    @discardableResult
    func importLive(_ incoming: [Sponsor]) -> Int {
        let have = Set(sponsors.map { $0.slug }.filter { !$0.isEmpty })
        let fresh = incoming.filter { !$0.slug.isEmpty && !have.contains($0.slug) }
        sponsors.append(contentsOf: fresh)
        if !fresh.isEmpty { save() }
        return fresh.count
    }
}
