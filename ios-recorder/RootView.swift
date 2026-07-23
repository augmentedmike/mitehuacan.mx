import SwiftUI

/// App shell: the top-level switcher between the app's sections — **Rutas** (record
/// + edit combi routes), **Patrocinadores** (sponsor data entry), and **Calcomanías**
/// (scan a sticker QR, mark where it went). Growing into a new section later is one
/// more `.tabItem` here; each area keeps its own NavigationStack, toolbar, and store,
/// so nothing else changes.
struct RootView: View {
    var body: some View {
        TabView {
            RouteListView()
                .tabItem { Label("Rutas", systemImage: "bus.fill") }
            SponsorListView()
                .tabItem { Label("Patrocinadores", systemImage: "storefront.fill") }
            StickerAdminView()
                .tabItem { Label("Calcomanías", systemImage: "qrcode.viewfinder") }
        }
    }
}
