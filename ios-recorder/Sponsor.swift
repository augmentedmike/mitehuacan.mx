import Foundation
import CoreLocation

/// One physical location for a sponsor — the pin that lands on the public map once
/// the sponsor is publishable. `serverId` matches `sponsor_locations.id` in prod so
/// a re-sync can line local edits up with the server row.
struct SponsorLocation: Codable, Identifiable, Hashable {
    var id = UUID()
    var serverId: Int? = nil
    var label: String = ""        // "sucursal centro", "1 Oriente"
    var lat: Double
    var lon: Double
    var active: Bool = true

    var coord: CLLocationCoordinate2D { .init(latitude: lat, longitude: lon) }
}

/// A sponsor (advertiser) entered by hand: identity, contact, logo, and locations.
/// No payments live here — this is pure data entry. Whether a sponsor's pins show on
/// the map is decided server-side (barter publishes on sync; paid needs a signed
/// contract), so the app never touches money — it just captures the facts.
struct Sponsor: Codable, Identifiable, Hashable {
    var id = UUID()
    var slug: String = ""              // stable key (matches sponsors.slug in prod)
    var name: String = ""
    var contactName: String = ""
    var contactEmail: String = ""
    var phone: String = ""
    var tier: String = "barter"        // barter | paid
    var notes: String = ""
    var active: Bool = true
    var logoData: Data? = nil          // PNG, downscaled on entry; synced as a data URL
    var locations: [SponsorLocation] = []
    var pendingSync = false            // has local changes not yet pushed to prod
    var createdAt = Date()

    var subtitle: String {
        var parts: [String] = []
        let n = locations.count
        if n > 0 { parts.append("\(n) ubicación\(n == 1 ? "" : "es")") }
        parts.append(tier == "barter" ? "Intercambio" : "Pagado")
        if !active { parts.append("Inactivo") }
        return parts.joined(separator: " · ")
    }
}

extension String {
    /// URL-safe slug: strip accents, lowercase, and collapse anything that isn't a
    /// letter or number into single dashes (no leading/trailing dashes).
    var slugified: String {
        let base = folding(options: .diacriticInsensitive, locale: .current).lowercased()
        let mapped = base.map { ($0.isLetter || $0.isNumber) ? $0 : "-" }
        return String(mapped).split(separator: "-").joined(separator: "-")
    }
}
