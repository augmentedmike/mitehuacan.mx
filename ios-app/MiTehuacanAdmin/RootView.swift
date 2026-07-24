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
    @EnvironmentObject var auth: AdminAuth
    @StateObject private var router = AppRouter()
    @State private var showSplash = true

    var body: some View {
        ZStack {
            if showSplash {
                SplashView().transition(.opacity)
            } else if auth.unlocked {
                Group {
                    switch router.section {
                    case .rutas:          RouteListView()
                    case .patrocinadores: SponsorListView()
                    case .calcomanias:    StickerAdminView()
                    case .negocios:       NegocioListView()
                    }
                }
            } else {
                LoginGateView()     // gate the whole app: user + PIN before any section
            }
        }
        .environmentObject(router)
        .task {
            // Hold the dancer splash for at least 3s. The native LaunchScreen is
            // instant once cached, so this SwiftUI splash (identical: dancer on
            // white) continues it seamlessly, then reveals login/app.
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            withAnimation(.easeInOut(duration: 0.35)) { showSplash = false }
        }
    }
}

/// Full-screen dancer splash — matches LaunchScreen.storyboard so the native
/// launch flows into it without a seam. Shown for a guaranteed minimum time.
struct SplashView: View {
    var body: some View {
        ZStack {
            Color.white.ignoresSafeArea()
            Image("LaunchLogo").resizable().scaledToFit()
                .frame(width: 200, height: 200)
        }
    }
}

/// The entry screen: nobody sees a section until they sign in. Reuses AdminAuth
/// (user "michael" + PIN validated by /api/admin/login). If a token is already in
/// the Keychain from a prior sign-in, `auth.unlocked` is true at launch and this
/// screen is skipped.
struct LoginGateView: View {
    @EnvironmentObject var auth: AdminAuth
    @State private var pin = ""

    var body: some View {
        VStack(spacing: 16) {
            Spacer()
            Text("MiTehuacán Admin").font(.title2.weight(.bold))
            Text("Inicia sesión").font(.subheadline).foregroundStyle(.secondary)

            VStack(spacing: 12) {
                HStack {
                    Image(systemName: "person.fill").foregroundStyle(.secondary)
                    Text(AdminAuth.user); Spacer()
                }
                .padding(12)
                .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))

                SecureField("PIN", text: $pin)
                    .keyboardType(.numberPad).textContentType(.password)
                    .submitLabel(.go).onSubmit(submit)
                    .padding(12)
                    .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))

                if !auth.error.isEmpty {
                    Text(auth.error).foregroundStyle(.red).font(.footnote)
                }
                Button(action: submit) {
                    HStack { if auth.busy { ProgressView() }; Text("Entrar").fontWeight(.semibold) }
                        .frame(maxWidth: .infinity).padding(.vertical, 12)
                }
                .buttonStyle(.borderedProminent)
                .disabled(pin.isEmpty || auth.busy)
            }
            .frame(maxWidth: 340)

            Spacer(); Spacer()
        }
        .padding()
    }

    private func submit() { Task { _ = await auth.unlock(pin: pin) } }
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
