import Foundation
import Combine

/// Local log of sticker placements captured in the field (JSON in Documents), with
/// the same pending/reconcile bookkeeping as routes and sponsors. Placements are
/// captured offline and pushed to prod when a connection + unlock is available.
final class StickerStore: ObservableObject {
    @Published var placements: [StickerPlacement] = []

    private var url: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("stickers.json")
    }

    init() { load() }

    func load() {
        guard let data = try? Data(contentsOf: url),
              let p = try? JSONDecoder().decode([StickerPlacement].self, from: data) else { return }
        placements = p
    }
    func save() {
        if let data = try? JSONEncoder().encode(placements) { try? data.write(to: url) }
    }

    var pendingCount: Int { placements.filter { $0.pendingSync }.count }
    func markSynced(_ id: StickerPlacement.ID) {
        if let i = placements.firstIndex(where: { $0.id == id }) { placements[i].pendingSync = false; save() }
    }

    /// Insert or update a placement, keyed by the sticker code (re-scanning the same
    /// code updates its placement instead of duplicating it). Always flags pending.
    func upsert(_ p: StickerPlacement) {
        var x = p; x.pendingSync = true
        if let i = placements.firstIndex(where: { $0.code == x.code }) {
            x.id = placements[i].id
            placements[i] = x
        } else {
            placements.insert(x, at: 0)
        }
        save()
    }

    func delete(_ p: StickerPlacement) { placements.removeAll { $0.id == p.id }; save() }
}
