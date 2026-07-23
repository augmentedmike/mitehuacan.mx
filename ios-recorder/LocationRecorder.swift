import Foundation
import CoreLocation
import Combine

/// GPS recorder that keeps logging while the phone is locked / the app is in the
/// background — the whole reason this is native. Requires (in Info.plist):
///   NSLocationWhenInUseUsageDescription
///   NSLocationAlwaysAndWhenInUseUsageDescription
///   UIBackgroundModes -> location
final class LocationRecorder: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var recording = false
    @Published var current: CLLocation?          // latest fix (for the map dot)
    @Published var points: [TrackPoint] = []     // the ride being recorded now
    @Published var authorized = false
    @Published var lastError: String?

    private let mgr = CLLocationManager()

    override init() {
        super.init()
        mgr.delegate = self
        mgr.desiredAccuracy = kCLLocationAccuracyBest
        mgr.distanceFilter = 8                    // a fix every ~8 m
        mgr.activityType = .automotiveNavigation
        mgr.pausesLocationUpdatesAutomatically = false
        mgr.requestWhenInUseAuthorization()
    }

    func requestAlways() { mgr.requestAlwaysAuthorization() }

    func start() {
        points = []
        recording = true
        // background updates need Always auth + the plist background mode
        mgr.allowsBackgroundLocationUpdates = true
        mgr.showsBackgroundLocationIndicator = true
        mgr.startUpdatingLocation()
    }

    /// Stop and return the recorded ride as a segment (to append to a Route).
    @discardableResult
    func stop() -> [TrackPoint] {
        recording = false
        mgr.stopUpdatingLocation()
        mgr.allowsBackgroundLocationUpdates = false
        return points
    }

    // MARK: CLLocationManagerDelegate
    func locationManagerDidChangeAuthorization(_ m: CLLocationManager) {
        switch m.authorizationStatus {
        case .authorizedAlways: authorized = true
        case .authorizedWhenInUse: authorized = true            // works foreground; ask for Always to record asleep
        case .denied, .restricted: authorized = false; lastError = "Ubicación denegada — actívala en Ajustes"
        default: authorized = false
        }
    }

    func locationManager(_ m: CLLocationManager, didUpdateLocations locs: [CLLocation]) {
        guard let loc = locs.last else { return }
        current = loc
        guard recording else { return }
        // drop wild fixes; keep everything else so nothing is lost
        guard loc.horizontalAccuracy >= 0, loc.horizontalAccuracy < 60 else { return }
        points.append(TrackPoint(lat: loc.coordinate.latitude,
                                 lon: loc.coordinate.longitude,
                                 ts: loc.timestamp,
                                 acc: loc.horizontalAccuracy,
                                 speed: loc.speed))
    }

    func locationManager(_ m: CLLocationManager, didFailWithError error: Error) {
        lastError = error.localizedDescription
    }
}
