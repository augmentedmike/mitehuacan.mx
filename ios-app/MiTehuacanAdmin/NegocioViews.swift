import SwiftUI

/// The "Negocios" section: the review queue for self-registered businesses.
/// Listings publish on submit, so this is review-after-the-fact:
///   • Aprobar  — clears it from the queue; it stays live in the directory.
///   • Rechazar — hides it (goes dark) and clears it from the queue.
struct NegocioListView: View {
    @EnvironmentObject var store: NegocioStore
    @EnvironmentObject var auth: AdminAuth
    @State private var showUnlock = false
    @State private var confirmReject: Negocio? = nil

    var body: some View {
        NavigationStack {
            Group {
                if store.loading && store.pending.isEmpty {
                    ProgressView("Cargando…")
                } else if store.pending.isEmpty {
                    ContentUnavailableView {
                        Label("Todo revisado", systemImage: "checkmark.seal")
                    } description: {
                        Text("No hay negocios por revisar. Los nuevos registros del directorio aparecerán aquí.")
                    } actions: {
                        Button { Task { await reload() } } label: {
                            Label("Actualizar", systemImage: "arrow.clockwise")
                        }
                    }
                } else {
                    List {
                        if !store.error.isEmpty {
                            Text(store.error).font(.caption).foregroundStyle(.red)
                        }
                        ForEach(store.pending) { n in
                            NegocioRow(n: n,
                                       onApprove: { act(n, "approve") },
                                       onReject: { confirmReject = n })
                        }
                    }
                    .listStyle(.plain)
                    .refreshable { await reload() }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) { SectionTitle() }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { Task { await reload() } } label: { Image(systemName: "arrow.clockwise") }
                        .disabled(store.loading)
                }
            }
            .task { await reload() }
            .sheet(isPresented: $showUnlock) { UnlockView { Task { await reload() } } }
            .confirmationDialog(
                "¿Rechazar \(confirmReject?.name ?? "")?",
                isPresented: Binding(get: { confirmReject != nil }, set: { if !$0 { confirmReject = nil } }),
                titleVisibility: .visible
            ) {
                Button("Rechazar y ocultar", role: .destructive) {
                    if let n = confirmReject { act(n, "reject") }
                    confirmReject = nil
                }
                Button("Cancelar", role: .cancel) { confirmReject = nil }
            } message: {
                Text("Dejará de mostrarse en el directorio público.")
            }
        }
    }

    private func reload() async {
        guard let token = auth.token else { showUnlock = true; return }
        await store.load(token: token)
    }

    private func act(_ n: Negocio, _ action: String) {
        guard let token = auth.token else { showUnlock = true; return }
        Task {
            let stale = await store.review(n, action: action, token: token)
            if stale { auth.lock(); showUnlock = true }
        }
    }
}

/// One pending listing: what the business submitted, plus Aprobar / Rechazar.
private struct NegocioRow: View {
    let n: Negocio
    var onApprove: () -> Void
    var onReject: () -> Void

    private var meta: String {
        [n.colonia, n.hours, n.serviceArea].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: " · ")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(n.name).font(.headline)

            if !n.categories.isEmpty || (n.categoryOther?.isEmpty == false) {
                let extra = n.categoryOther.map { n.categories.isEmpty ? $0 : " · \($0)" } ?? ""
                Text(n.categories + extra).font(.caption).foregroundStyle(.secondary)
            }
            if let d = n.description, !d.isEmpty {
                Text(d).font(.subheadline).lineLimit(4)
            }
            if !meta.isEmpty {
                Text(meta).font(.caption).foregroundStyle(.secondary)
            }
            HStack(spacing: 12) {
                if !n.contactDigits.isEmpty {
                    Link(destination: URL(string: "https://wa.me/52\(n.contactDigits)")!) {
                        Label(n.contactDigits, systemImage: "message.fill").font(.caption)
                    }
                }
                if let b = n.qrBatch, !b.isEmpty {
                    Text("QR: \(b)").font(.caption2).foregroundStyle(.secondary)
                }
                Spacer()
            }

            HStack(spacing: 12) {
                Button(action: onApprove) {
                    Label("Aprobar", systemImage: "checkmark").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent).tint(.green)
                Button(action: onReject) {
                    Label("Rechazar", systemImage: "xmark").frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered).tint(.red)
            }
            .padding(.top, 2)
        }
        .padding(.vertical, 6)
        .buttonStyle(.automatic)   // keep the two buttons independently tappable in a List row
    }
}
