import Foundation
import CoreLocation

/// One placement of a printed QR sticker, captured in the field: the scanned code
/// plus where it went. Location is **optional by design** — a sticker with no
/// location is on something that moves (a combi), so the backend infers
/// `placement = combi`; a sticker with lat/lon is `fijo` (a fixed spot).
struct StickerPlacement: Codable, Identifiable, Hashable {
    var id = UUID()
    var code: String = ""              // the sticker id, e.g. "TEH-0019"
    var lat: Double? = nil             // nil = moves (combi)
    var lon: Double? = nil
    var routeId: String = ""           // optional: which line, when known
    var unitDesc: String = ""          // "combi blanca, placa SXY-123-A"
    var notes: String = ""
    var placedAt = Date()
    var pendingSync = false            // not yet saved to prod

    var hasLocation: Bool { lat != nil && lon != nil }
    var coord: CLLocationCoordinate2D? {
        guard let lat, let lon else { return nil }
        return .init(latitude: lat, longitude: lon)
    }

    var subtitle: String {
        var parts: [String] = []
        parts.append(hasLocation ? "Fijo" : "En movimiento (combi)")
        if !routeId.isEmpty { parts.append("Ruta \(routeId)") }
        return parts.joined(separator: " · ")
    }
}

/// Pull a sticker code out of whatever the camera read: a full `/qr/<id>` URL or a
/// bare code. Normalized exactly like the server resolver (uppercase, [A-Z0-9-],
/// max 20) so what we save matches what a scan of the same code resolves to.
func stickerCode(from raw: String) -> String? {
    let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
    var candidate = trimmed
    if let url = URL(string: trimmed),
       let qr = url.pathComponents.firstIndex(of: "qr"),
       qr + 1 < url.pathComponents.count {
        candidate = url.pathComponents[qr + 1]
    } else if let last = trimmed.split(separator: "/").last {
        candidate = String(last)
    }
    let norm = candidate.uppercased().filter { $0.isLetter || $0.isNumber || $0 == "-" }
    return norm.isEmpty ? nil : String(norm.prefix(20))
}
