import Foundation
import CoreLocation

// A single GPS fix in a recorded ride.
struct TrackPoint: Codable, Identifiable, Hashable {
    var id = UUID()
    var lat: Double
    var lon: Double
    var ts: Date
    var acc: Double          // horizontal accuracy (m)
    var speed: Double        // m/s, -1 if unknown

    var coord: CLLocationCoordinate2D { .init(latitude: lat, longitude: lon) }
}

// Schedule for one day-type at a stop: first/last departure + headway.
struct DaySchedule: Codable, Hashable {
    var first: String = ""       // "06:00"
    var last: String = ""        // "22:00"
    var intervalMin: Int = 0     // headway in minutes (0 = unknown)
}

// The metadata you enter by hand at each major stop.
struct StopSchedule: Codable, Hashable {
    var weekday = DaySchedule()   // Lun–Vie
    var saturday = DaySchedule()
    var sunday = DaySchedule()
}

enum StopKind: String, Codable, CaseIterable {
    case origin      // downtown terminal / start
    case major       // a major stop along the way
    case last        // last stop / end of line
    var label: String {
        switch self {
        case .origin: return "Origen"
        case .major:  return "Parada mayor"
        case .last:   return "Última parada"
        }
    }
}

// A stop the driver/rider marks on the route, with its schedule.
struct Stop: Codable, Identifiable, Hashable {
    var id = UUID()
    var name: String = ""
    var lat: Double
    var lon: Double
    var kind: StopKind = .major
    var schedule = StopSchedule()

    var coord: CLLocationCoordinate2D { .init(latitude: lat, longitude: lon) }
}

// A recorded route. `segments` holds one array of points per recorded ride —
// join merges rides, snip trims a segment, so partial rides aggregate into one line.
struct Route: Codable, Identifiable, Hashable {
    var id = UUID()
    var serverId: String? = nil    // matches the live routes.js feature id (nil = recorded locally)
    var color: String? = nil       // route color from the live data
    var kind: String? = nil        // local / foránea / etc.
    var name: String = "Ruta sin nombre"
    var lineName: String = ""      // número / nombre de la ruta (ej. "Ruta 5")
    var origin: String = ""        // terminal de origen
    var destination: String = ""   // destino
    var notes: String = ""
    var createdAt = Date()
    var segments: [[TrackPoint]] = []   // each element = one recorded ride
    var stops: [Stop] = []
    var schedule = StopSchedule()       // service schedule for the whole route
                                        // (weekday/Sat/Sun first, last, interval)
    var pendingSync = false             // has local changes not yet pushed to prod
    var fare: Int? = nil                // costo por tramo (MXN); intercity varies by cities

    // all points flattened in order — the route line
    var line: [TrackPoint] { segments.flatMap { $0 } }
    var pointCount: Int { segments.reduce(0) { $0 + $1.count } }

    var km: Double { segments.reduce(0) { $0 + $1.km } }
}

extension Array where Element == TrackPoint {
    // distance of this point sequence in km
    var km: Double {
        var d = 0.0
        for (a, b) in zip(self, dropFirst()) {
            d += CLLocation(latitude: a.lat, longitude: a.lon)
                .distance(from: CLLocation(latitude: b.lat, longitude: b.lon))
        }
        return d / 1000
    }
}
