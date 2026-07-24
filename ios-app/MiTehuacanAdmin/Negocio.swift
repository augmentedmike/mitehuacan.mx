import Foundation

/// One self-registered business awaiting review in the admin app. It mirrors the
/// public intake row (`negocios`) minus the internal bits. Listings publish on
/// submit; here the admin either Approves (it stays live, leaves the queue) or
/// Denies (it goes dark). Read-only value — the app never edits the business.
struct Negocio: Codable, Identifiable, Hashable {
    let id: Int
    var name: String = ""
    var category: String = ""
    var category2: String? = nil
    var categoryOther: String? = nil
    var description: String? = nil
    var ownerName: String? = nil
    var whatsapp: String? = nil
    var phone: String? = nil
    var email: String? = nil
    var facebook: String? = nil
    var instagram: String? = nil
    var website: String? = nil
    var hasLocation: Int? = nil
    var lat: Double? = nil
    var lon: Double? = nil
    var address: String? = nil
    var colonia: String? = nil
    var serviceArea: String? = nil
    var hours: String? = nil
    var priceFrom: Double? = nil
    var priceNote: String? = nil
    var fiesta: Int? = nil
    var qrBatch: String? = nil
    var createdAt: String? = nil

    enum CodingKeys: String, CodingKey {
        case id, name, category, category2, description, whatsapp, phone, email
        case facebook, instagram, website, lat, lon, address, colonia, hours, fiesta
        case categoryOther = "category_other"
        case ownerName = "owner_name"
        case hasLocation = "has_location"
        case serviceArea = "service_area"
        case priceFrom = "price_from"
        case priceNote = "price_note"
        case qrBatch = "qr_batch"
        case createdAt = "created_at"
    }

    /// Best contact number for a WhatsApp/tel action (digits only).
    var contactDigits: String {
        (whatsapp ?? phone ?? "").filter(\.isNumber)
    }
    var categories: String {
        [category, category2].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: " · ")
    }
}
