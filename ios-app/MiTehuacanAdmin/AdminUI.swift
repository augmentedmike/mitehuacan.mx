import SwiftUI

/// Enter the admin PIN to unlock writing to production. User is fixed to "michael";
/// the PIN is validated by /api/admin/login and kept in the Keychain.
struct UnlockView: View {
    @EnvironmentObject var auth: AdminAuth
    @Environment(\.dismiss) private var dismiss
    @State private var pin = ""
    var onUnlocked: () -> Void = {}

    var body: some View {
        NavigationStack {
            Form {
                Section("Cuenta admin") {
                    LabeledContent("Usuario", value: AdminAuth.user)
                    SecureField("PIN", text: $pin)
                        .keyboardType(.numberPad)
                        .textContentType(.password)
                }
                if !auth.error.isEmpty {
                    Text(auth.error).foregroundStyle(.red).font(.footnote)
                }
                Section {
                    Button {
                        Task { if await auth.unlock(pin: pin) { onUnlocked(); dismiss() } }
                    } label: {
                        HStack { if auth.busy { ProgressView() }; Text("Desbloquear") }
                    }
                    .disabled(pin.isEmpty || auth.busy)
                } footer: {
                    Text("Solo el admin puede escribir a producción. Grabar y ver rutas no requiere PIN.")
                }
            }
            .navigationTitle("Desbloquear escritura")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } } }
        }
    }
}

/// Push locally-changed routes to production. Phase 1 pushes metadata + schedule
/// for existing lines; new geometry is flagged for Phase 2.
struct ReconcileView: View {
    @EnvironmentObject var store: RouteStore
    @EnvironmentObject var auth: AdminAuth
    @Environment(\.dismiss) private var dismiss
    @State private var running = false
    @State private var log: [String] = []

    private var pending: [Route] { store.routes.filter { $0.pendingSync } }

    var body: some View {
        NavigationStack {
            List {
                Section("\(pending.count) por subir") {
                    if pending.isEmpty {
                        Text("Todo sincronizado con producción").foregroundStyle(.secondary)
                    } else {
                        ForEach(pending) { r in
                            VStack(alignment: .leading, spacing: 2) {
                                Text(r.name).font(.headline)
                                Text(r.serverId == nil ? "Ruta nueva · geometría (Fase 2)" : "Horario + información")
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                if !log.isEmpty { Section("Resultado") { ForEach(log, id: \.self) { Text($0).font(.footnote) } } }
            }
            .navigationTitle("Reconciliar")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cerrar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button { Task { await push() } } label: {
                        HStack { if running { ProgressView() }; Text("Subir") }
                    }.disabled(pending.isEmpty || running || !auth.unlocked)
                }
            }
        }
    }

    @MainActor private func push() async {
        guard let token = auth.token else { auth.lock(); return }
        running = true; log = []
        for r in pending {
            guard r.serverId != nil else { log.append("• \(r.name): geometría nueva → Fase 2"); continue }
            do {
                try await RouteSync.pushLine(r, token: token)
                store.markSynced(r.id)
                log.append("✓ \(r.name)")
            } catch {
                log.append("✗ \(r.name): \(error.localizedDescription)")
                if case RouteSync.SyncError.unauthorized = error { auth.lock() }
            }
        }
        running = false
    }
}
