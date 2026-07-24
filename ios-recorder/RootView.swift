import SwiftUI
import Combine

/// The app's sections. Add a case here (and its view in `RootView`) to grow the app —
/// the title dropdown picks it up automatically.
enum AppSection: String, CaseIterable, Identifiable {
    case rutas = "Rutas"
    case patrocinadores = "Patrocinadores"
    case calcomanias = "Calcomanías"
    case negocios = "Negocios"

    var id: String { rawValue }
    var icon: String {
        switch self {
        case .rutas:          return "bus.fill"
        case .patrocinadores: return "storefront.fill"
        case .calcomanias:    return "qrcode.viewfinder"
        case .negocios:       return "checklist"
        }
    }
}

/// Holds which section is showing. Injected into every section so the title
/// dropdown can switch from anywhere.
final class AppRouter: ObservableObject {
    @Published var section: AppSection = .rutas
}

/// App shell: shows one section at a time. The switcher is the screen title itself —
/// tap "Rutas ⌄" to drop down and jump to Patrocinadores or Calcomanías.
struct RootView: View {
    @StateObject private var router = AppRouter()

    var body: some View {
        Group {
            switch router.section {
            case .rutas:          RouteListView()
            case .patrocinadores: SponsorListView()
            case .calcomanias:    StickerAdminView()
            case .negocios:       NegocioListView()
            }
        }
        .environmentObject(router)
    }
}

/// The tappable navigation title used by every section (in the `.principal` toolbar
/// slot). Shows "<Section> ⌄" and opens a menu to switch. Because only the active
/// section is on screen, it always reflects and controls the current selection.
struct SectionTitle: View {
    @EnvironmentObject var router: AppRouter

    var body: some View {
        Menu {
            Picker("Sección", selection: $router.section) {
                ForEach(AppSection.allCases) { s in
                    Label(s.rawValue, systemImage: s.icon).tag(s)
                }
            }
        } label: {
            HStack(spacing: 4) {
                Text(router.section.rawValue).font(.headline)
                Image(systemName: "chevron.down").font(.caption2.weight(.bold)).foregroundStyle(.secondary)
            }
            .contentShape(Rectangle())
        }
        .foregroundStyle(.primary)
    }
}
