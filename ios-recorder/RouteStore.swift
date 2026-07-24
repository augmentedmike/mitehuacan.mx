import Foundation
import Combine

/// Local persistence for recorded routes (JSON in the app's Documents dir) plus
/// the editing ops: join (merge rides), snip (trim a segment), prune (drop points
/// / segments / routes). No server; export happens later.
final class RouteStore: ObservableObject {
    @Published var routes: [Route] = []

    private var url: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("routes.json")
    }

    init() { load() }

    /// Decode off the main thread so it never blocks app launch (a large routes.json
    /// used to freeze the first frame for seconds); publish on main when ready.
    func load() {
        let u = url
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let data = try? Data(contentsOf: u),
                  let r = try? JSONDecoder().decode([Route].self, from: data) else { return }
            DispatchQueue.main.async { self?.routes = r }
        }
    }

    func save() {
        if let data = try? JSONEncoder().encode(routes) { try? data.write(to: url) }
    }

    // routes with local edits not yet pushed to production
    var pendingCount: Int { routes.filter { $0.pendingSync }.count }
    func markSynced(_ id: Route.ID) {
        if let i = routes.firstIndex(where: { $0.id == id }) { routes[i].pendingSync = false; save() }
    }

    // MARK: create / prune
    func add(_ route: Route) { var r = route; r.pendingSync = true; routes.insert(r, at: 0); save() }

    /// Merge live routes: add any whose serverId we don't already have, so a
    /// re-sync never clobbers local edits or freshly recorded routes. Returns #added.
    @discardableResult
    func importLive(_ incoming: [Route]) -> Int {
        let have = Set(routes.compactMap { $0.serverId })
        let fresh = incoming.filter { r in r.serverId.map { !have.contains($0) } ?? true }
        routes.append(contentsOf: fresh)
        if !fresh.isEmpty { save() }
        return fresh.count
    }
    func delete(_ route: Route) { routes.removeAll { $0.id == route.id }; save() }

    func update(_ route: Route) {
        if let i = routes.firstIndex(where: { $0.id == route.id }) {
            routes[i] = route; routes[i].pendingSync = true; save()
        }
    }

    /// New route from a freshly recorded ride.
    func routeFromRide(_ pts: [TrackPoint], name: String) -> Route {
        Route(name: name.isEmpty ? "Ruta \(routes.count + 1)" : name, segments: pts.isEmpty ? [] : [pts])
    }

    // MARK: JOIN — append a ride as a new segment (partial rides aggregate into one line)
    func appendRide(_ pts: [TrackPoint], to routeID: Route.ID) {
        guard !pts.isEmpty, let i = routes.firstIndex(where: { $0.id == routeID }) else { return }
        routes[i].segments.append(pts)
        orderSegments(&routes[i])
        routes[i].pendingSync = true
        save()
    }

    /// Merge one whole route's segments into another (join two recordings).
    func merge(_ src: Route, into dstID: Route.ID) {
        guard let i = routes.firstIndex(where: { $0.id == dstID }) else { return }
        routes[i].segments.append(contentsOf: src.segments)
        routes[i].stops.append(contentsOf: src.stops)
        orderSegments(&routes[i])
        routes[i].pendingSync = true
        delete(src)
        save()
    }

    /// Chain segments head-to-tail so the joined line flows in one direction:
    /// greedily order by nearest endpoints. Rough but good enough for hand-editing.
    private func orderSegments(_ route: inout Route) {
        var segs = route.segments.filter { !$0.isEmpty }
        guard segs.count > 1 else { route.segments = segs; return }
        var ordered = [segs.removeFirst()]
        while !segs.isEmpty {
            let tail = ordered.last!.last!
            // pick the remaining segment whose start OR end is closest to the current tail
            var bestIdx = 0, bestDist = Double.greatestFiniteMagnitude, flip = false
            for (idx, s) in segs.enumerated() {
                let dStart = dist(tail, s.first!)
                let dEnd = dist(tail, s.last!)
                if dStart < bestDist { bestDist = dStart; bestIdx = idx; flip = false }
                if dEnd < bestDist { bestDist = dEnd; bestIdx = idx; flip = true }
            }
            var next = segs.remove(at: bestIdx)
            if flip { next.reverse() }
            ordered.append(next)
        }
        route.segments = ordered
    }

    // MARK: SNIP — trim a segment to a [start, end] index range
    func snip(routeID: Route.ID, segment: Int, keep range: ClosedRange<Int>) {
        guard let i = routes.firstIndex(where: { $0.id == routeID }),
              segment < routes[i].segments.count else { return }
        let seg = routes[i].segments[segment]
        let lo = max(0, range.lowerBound), hi = min(seg.count - 1, range.upperBound)
        guard lo <= hi else { return }
        routes[i].segments[segment] = Array(seg[lo...hi])
        routes[i].pendingSync = true
        save()
    }

    func deleteSegment(routeID: Route.ID, segment: Int) {
        guard let i = routes.firstIndex(where: { $0.id == routeID }),
              segment < routes[i].segments.count else { return }
        routes[i].segments.remove(at: segment)
        routes[i].pendingSync = true
        save()
    }

    private func dist(_ a: TrackPoint, _ b: TrackPoint) -> Double {
        let dlat = (a.lat - b.lat) * 111_000
        let dlon = (a.lon - b.lon) * 105_000
        return (dlat * dlat + dlon * dlon).squareRoot()
    }
}
