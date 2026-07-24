import SwiftUI

@main
struct RutasRecorderApp: App {
    @StateObject private var store = RouteStore()
    @StateObject private var sponsors = SponsorStore()
    @StateObject private var stickers = StickerStore()
    @StateObject private var negocios = NegocioStore()
    @StateObject private var recorder = LocationRecorder()
    @StateObject private var auth = AdminAuth()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(store)
                .environmentObject(sponsors)
                .environmentObject(stickers)
                .environmentObject(negocios)
                .environmentObject(recorder)
                .environmentObject(auth)
        }
    }
}
