import SwiftUI
import MapKit

// MARK: - Stickers tab: scan → locate → save

struct StickerAdminView: View {
    @EnvironmentObject var store: StickerStore
    @EnvironmentObject var auth: AdminAuth
    @EnvironmentObject var recorder: LocationRecorder

    @State private var showScanner = false
    @State private var pendingScan: String? = nil
    @State private var editing: StickerPlacement? = nil
    @State private var showManual = false
    @State private var manualCode = ""
    @State private var query = ""
    @State private var status = ""
    @State private var showUnlock = false
    @State private var showReconcile = false
    @State private var afterUnlock: Intent = .reconcile

    private enum Intent { case reconcile }

    private var filtered: [StickerPlacement] {
        store.placements.filter { p in
            query.isEmpty || [p.code, p.routeId, p.unitDesc].contains { $0.localizedCaseInsensitiveContains(query) }
        }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                scanBar
                if store.placements.isEmpty {
                    ContentUnavailableView {
                        Label("Sin calcomanías registradas", systemImage: "qrcode.viewfinder")
                    } description: {
                        Text("Escanea el QR de una calcomanía y marca dónde la pegaste. Sin ubicación = va en un combi (se mueve).")
                    }
                    .frame(maxHeight: .infinity)
                } else {
                    List {
                        if !status.isEmpty {
                            Section { Text(status).font(.footnote).foregroundStyle(.secondary) }
                        }
                        ForEach(filtered) { p in
                            Button { editing = p } label: { row(p) }.buttonStyle(.plain)
                        }
                        .onDelete { idx in idx.map { filtered[$0] }.forEach(store.delete) }
                        if filtered.isEmpty { Text("Ninguna coincide").foregroundStyle(.secondary) }
                    }
                    .listStyle(.plain)
                    .searchable(text: $query, prompt: "Buscar código, ruta o unidad")
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) { SectionTitle() }
                ToolbarItem(placement: .primaryAction) {
                    Button { showManual = true } label: { Label("Código manual", systemImage: "keyboard") }
                }
                if store.pendingCount > 0 {
                    ToolbarItem(placement: .bottomBar) {
                        Button {
                            if auth.unlocked { showReconcile = true } else { afterUnlock = .reconcile; showUnlock = true }
                        } label: {
                            Label("\(store.pendingCount) por subir · Reconciliar", systemImage: "arrow.up.circle.fill")
                        }.tint(.orange)
                    }
                }
            }
            .sheet(isPresented: $showScanner, onDismiss: handleScan) {
                QRScannerView { value in
                    pendingScan = value; showScanner = false
                } onDenied: {
                    pendingScan = "\u{0}denied"; showScanner = false
                }
                .ignoresSafeArea()
                .overlay(alignment: .top) {
                    Text("Apunta al QR de la calcomanía")
                        .font(.subheadline.weight(.medium)).padding(10)
                        .background(.ultraThinMaterial, in: Capsule()).padding(.top, 60)
                }
                .overlay(alignment: .bottom) {
                    Button("Cancelar") { showScanner = false }
                        .buttonStyle(.borderedProminent).padding(.bottom, 40)
                }
            }
            .sheet(item: $editing) { p in
                StickerPlacementEditor(placement: p) { commit($0) }
            }
            .sheet(isPresented: $showReconcile) { StickerReconcileView() }
            .sheet(isPresented: $showUnlock) { UnlockView { showReconcile = true } }
            .alert("Código de calcomanía", isPresented: $showManual) {
                TextField("TEH-0019", text: $manualCode)
                    .textInputAutocapitalization(.characters).autocorrectionDisabled()
                Button("Continuar") {
                    if let code = stickerCode(from: manualCode) { editing = StickerPlacement(code: code) }
                    manualCode = ""
                }
                Button("Cancelar", role: .cancel) { manualCode = "" }
            } message: { Text("Escribe el código impreso en la calcomanía.") }
        }
    }

    private var scanBar: some View {
        Button { recorder.requestAlways(); showScanner = true } label: {
            Label("Escanear calcomanía", systemImage: "qrcode.viewfinder")
                .font(.title3.bold()).frame(maxWidth: .infinity).padding(.vertical, 8)
        }
        .buttonStyle(.borderedProminent)
        .padding(.horizontal, 12).padding(.vertical, 10)
        .background(.bar)
    }

    private func row(_ p: StickerPlacement) -> some View {
        HStack(spacing: 12) {
            Image(systemName: p.hasLocation ? "mappin.circle.fill" : "bus.fill")
                .font(.title3).foregroundStyle(p.hasLocation ? .blue : .purple)
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(p.code).font(.headline.monospaced())
                    if p.pendingSync {
                        Image(systemName: "arrow.up.circle.fill").font(.caption).foregroundStyle(.orange)
                    }
                }
                Text(p.subtitle).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.caption).foregroundStyle(.tertiary)
        }
    }

    // scanner returns via onDismiss so the editor sheet presents cleanly afterward
    private func handleScan() {
        guard let raw = pendingScan else { return }
        pendingScan = nil
        if raw == "\u{0}denied" { showManual = true; return }
        if let code = stickerCode(from: raw) { editing = StickerPlacement(code: code) }
        else { status = "No se reconoció el código escaneado" }
    }

    private func commit(_ p: StickerPlacement) {
        store.upsert(p)
        guard let token = auth.token else { status = "Guardado local · desbloquea para subir \(p.code)"; return }
        Task { @MainActor in
            do {
                try await StickerSync.push(p, token: token)
                if let stored = store.placements.first(where: { $0.code == p.code }) { store.markSynced(stored.id) }
                status = "Guardado y subido: \(p.code)"
            } catch {
                if case StickerSync.SyncError.unauthorized = error { auth.lock() }
                status = "Guardado local (sin subir): \(error.localizedDescription)"
            }
        }
    }
}

// MARK: - Editor: code + optional location + details

struct StickerPlacementEditor: View {
    @EnvironmentObject var recorder: LocationRecorder
    @State private var draft: StickerPlacement
    @State private var hasLocation: Bool
    @State private var camera: MapCameraPosition
    var onSave: (StickerPlacement) -> Void
    @Environment(\.dismiss) private var dismiss

    init(placement: StickerPlacement, onSave: @escaping (StickerPlacement) -> Void) {
        _draft = State(initialValue: placement)
        self.onSave = onSave
        let has = placement.lat != nil && placement.lon != nil
        _hasLocation = State(initialValue: has)
        let center = CLLocationCoordinate2D(latitude: placement.lat ?? 18.462, longitude: placement.lon ?? -97.393)
        _camera = State(initialValue: .region(MKCoordinateRegion(
            center: center, span: MKCoordinateSpan(latitudeDelta: 0.02, longitudeDelta: 0.02))))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Calcomanía") {
                    HStack {
                        Image(systemName: "qrcode").foregroundStyle(.secondary)
                        TextField("TEH-0019", text: $draft.code)
                            .font(.body.monospaced())
                            .textInputAutocapitalization(.characters).autocorrectionDisabled()
                    }
                }

                Section {
                    Toggle("Ubicación fija", isOn: $hasLocation.animation())
                    if hasLocation {
                        MapReader { proxy in
                            Map(position: $camera) {
                                if let c = draft.coord { Marker("Aquí", coordinate: c) }
                            }
                            .frame(height: 220)
                            .onTapGesture { pt in
                                if let c = proxy.convert(pt, from: .local) { draft.lat = c.latitude; draft.lon = c.longitude }
                            }
                        }
                        Button {
                            if let c = recorder.current?.coordinate {
                                draft.lat = c.latitude; draft.lon = c.longitude
                                camera = .region(MKCoordinateRegion(center: c,
                                    span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)))
                            }
                        } label: { Label("Usar mi ubicación", systemImage: "location.fill") }
                        .disabled(recorder.current == nil)
                        if let c = draft.coord {
                            Text(String(format: "%.5f, %.5f", c.latitude, c.longitude))
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                } header: { Text("Ubicación") } footer: {
                    Text(hasLocation
                         ? "Fijo: toca el mapa para colocar el pin donde quedó la calcomanía."
                         : "Sin ubicación: se asume que va en algo que se mueve (combi).")
                }

                Section("Detalles (opcional)") {
                    TextField("Ruta (ej. 15)", text: $draft.routeId)
                        .autocorrectionDisabled()
                    TextField("Unidad (ej. combi blanca, placa SXY-123-A)", text: $draft.unitDesc)
                    TextField("Notas", text: $draft.notes, axis: .vertical).lineLimit(1...4)
                }
            }
            .navigationTitle(draft.code.isEmpty ? "Calcomanía" : draft.code)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Guardar") { save() }
                        .disabled(draft.code.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onChange(of: hasLocation) { _, on in
                if on {
                    if draft.lat == nil || draft.lon == nil {
                        let c = recorder.current?.coordinate
                        draft.lat = c?.latitude ?? 18.462
                        draft.lon = c?.longitude ?? -97.393
                    }
                    if let cc = draft.coord {
                        camera = .region(MKCoordinateRegion(center: cc,
                            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)))
                    }
                } else {
                    draft.lat = nil; draft.lon = nil
                }
            }
            .onAppear { recorder.requestAlways() }
        }
    }

    private func save() {
        var p = draft
        p.code = stickerCode(from: p.code) ?? p.code.trimmingCharacters(in: .whitespaces).uppercased()
        if !hasLocation { p.lat = nil; p.lon = nil }
        onSave(p)
        dismiss()
    }
}

// MARK: - Push pending placements to production

struct StickerReconcileView: View {
    @EnvironmentObject var store: StickerStore
    @EnvironmentObject var auth: AdminAuth
    @Environment(\.dismiss) private var dismiss
    @State private var running = false
    @State private var log: [String] = []

    private var pending: [StickerPlacement] { store.placements.filter { $0.pendingSync } }

    var body: some View {
        NavigationStack {
            List {
                Section("\(pending.count) por subir") {
                    if pending.isEmpty {
                        Text("Todo sincronizado con producción").foregroundStyle(.secondary)
                    } else {
                        ForEach(pending) { p in
                            VStack(alignment: .leading, spacing: 2) {
                                Text(p.code).font(.headline.monospaced())
                                Text(p.subtitle).font(.caption).foregroundStyle(.secondary)
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
        for p in pending {
            do {
                try await StickerSync.push(p, token: token)
                store.markSynced(p.id)
                log.append("✓ \(p.code)")
            } catch {
                log.append("✗ \(p.code): \(error.localizedDescription)")
                if case StickerSync.SyncError.unauthorized = error { auth.lock() }
            }
        }
        running = false
    }
}
