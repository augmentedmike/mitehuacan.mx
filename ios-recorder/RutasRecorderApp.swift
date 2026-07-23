import SwiftUI

@main
struct RutasRecorderApp: App {
    @StateObject private var store = RouteStore()
    @StateObject private var recorder = LocationRecorder()
    @StateObject private var auth = AdminAuth()

    var body: some Scene {
        WindowGroup {
            RouteListView()
                .environmentObject(store)
                .environmentObject(recorder)
                .environmentObject(auth)
        }
    }
}
