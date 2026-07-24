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

/// A business the admin is entering by hand (the "+" flow), before it exists on the
/// server. Mirrors the writable columns; `PUT /api/admin/negocios` inserts it live
/// and pre-approved. Location is optional — a fixed local pins the map; a mobile /
/// service business (plumber, DJ) skips it and shows by service area instead.
struct NegocioDraft {
    var name = ""
    var category = ""
    var category2 = ""
    var categoryOther = ""
    var description = ""
    var ownerName = ""
    var whatsapp = ""
    var phone = ""
    var email = ""
    var website = ""
    var facebook = ""
    var instagram = ""
    var colonia = ""
    var address = ""
    var serviceArea = ""
    var hours = ""
    var priceFrom = ""
    var priceNote = ""

    var hasLocation = false
    var lat = 18.462     // Tehuacán centro — a sane default pin
    var lon = -97.393

    var canSave: Bool {
        name.trimmingCharacters(in: .whitespaces).count >= 3 && !category.isEmpty
    }

    /// JSON body for the admin create endpoint. Empty strings are dropped so the
    /// server stores NULLs rather than blanks.
    var payload: [String: Any] {
        func s(_ v: String) -> String? {
            let t = v.trimmingCharacters(in: .whitespaces); return t.isEmpty ? nil : t
        }
        var b: [String: Any] = ["name": name.trimmingCharacters(in: .whitespaces), "category": category]
        b["category2"]      = s(category2)
        b["category_other"] = s(categoryOther)
        b["description"]    = s(description)
        b["owner_name"]     = s(ownerName)
        b["whatsapp"]       = s(whatsapp)
        b["phone"]          = s(phone)
        b["email"]          = s(email)
        b["website"]        = s(website)
        b["facebook"]       = s(facebook)
        b["instagram"]      = s(instagram)
        b["colonia"]        = s(colonia)
        b["address"]        = s(address)
        b["service_area"]   = s(serviceArea)
        b["hours"]          = s(hours)
        if let p = s(priceFrom), let v = Double(p) { b["price_from"] = v }
        b["price_note"]     = s(priceNote)
        if hasLocation { b["has_location"] = 1; b["lat"] = lat; b["lon"] = lon }
        return b.compactMapValues { $0 }
    }
}
