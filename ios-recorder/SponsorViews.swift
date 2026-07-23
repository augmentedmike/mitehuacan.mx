import SwiftUI
import MapKit
import PhotosUI
import UIKit

// MARK: - List of sponsors + entry point

struct SponsorListView: View {
    @EnvironmentObject var store: SponsorStore
    @EnvironmentObject var auth: AdminAuth
    @State private var showForm = false
    @State private var editing: Sponsor? = nil
    @State private var query = ""
    @State private var loading = false
    @State private var status = ""
    @State private var showUnlock = false
    @State private var showReconcile = false
    @State private var afterUnlock: Intent = .load

    private enum Intent { case load, reconcile }

    private var filtered: [Sponsor] {
        store.sponsors.filter { s in
            query.isEmpty
                || [s.name, s.slug, s.contactName].contains { $0.localizedCaseInsensitiveContains(query) }
        }
    }

    var body: some View {
        NavigationStack {
            Group {
                if store.sponsors.isEmpty {
                    ContentUnavailableView {
                        Label("Sin patrocinadores", systemImage: "storefront")
                    } description: {
                        Text("Agrega un patrocinador (logo, contacto y ubicaciones) o carga los que ya están en producción.")
                    } actions: {
                        VStack(spacing: 10) {
                            Button { showForm = true } label: { Label("Nuevo patrocinador", systemImage: "plus") }
                                .buttonStyle(.borderedProminent)
                            Button { startLoad() } label: {
                                if loading { ProgressView() } else { Label("Cargar de producción", systemImage: "arrow.down.circle") }
                            }.disabled(loading)
                        }
                    }
                } else {
                    VStack(spacing: 0) {
                        VStack(spacing: 8) {
                            TextField("Buscar por nombre, slug o contacto", text: $query)
                                .textFieldStyle(.roundedBorder)
                            if loading {
                                HStack(spacing: 6) {
                                    ProgressView().controlSize(.small)
                                    Text("Cargando…").font(.caption).foregroundStyle(.secondary)
                                    Spacer()
                                }
                            } else if !status.isEmpty {
                                HStack { Text(status).font(.caption).foregroundStyle(.secondary); Spacer() }
                            }
                        }
                        .padding(.horizontal, 12).padding(.top, 8).padding(.bottom, 6)
                        .background(.bar)

                        List {
                            ForEach(filtered) { s in
                                Button { editing = s } label: { sponsorRow(s) }
                                    .buttonStyle(.plain)
                            }
                            .onDelete { idx in idx.map { filtered[$0] }.forEach(store.delete) }
                            if filtered.isEmpty {
                                Text("Ningún patrocinador coincide").foregroundStyle(.secondary)
                            }
                        }
                        .listStyle(.plain)
                    }
                }
            }
            .navigationTitle("Patrocinadores")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { startLoad() } label: {
                        if loading { ProgressView() } else { Label("Cargar", systemImage: "arrow.down.circle") }
                    }.disabled(loading)
                }
                ToolbarItem(placement: .primaryAction) {
                    Button { showForm = true } label: { Label("Nuevo", systemImage: "plus") }
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
            .sheet(isPresented: $showForm) {
                SponsorFormView(sponsor: nil) { store.add($0) }
            }
            .sheet(item: $editing) { s in
                SponsorFormView(sponsor: s) { store.update($0) }
            }
            .sheet(isPresented: $showUnlock) {
                UnlockView {
                    switch afterUnlock {
                    case .load: Task { await load() }
                    case .reconcile: showReconcile = true
                    }
                }
            }
            .sheet(isPresented: $showReconcile) { SponsorReconcileView() }
        }
    }

    private func startLoad() {
        if auth.token != nil { Task { await load() } }
        else { afterUnlock = .load; showUnlock = true }
    }

    @MainActor private func load() async {
        guard let token = auth.token else { afterUnlock = .load; showUnlock = true; return }
        guard !loading else { return }
        loading = true; defer { loading = false }
        do {
            let live = try await SponsorSync.fetchLive(token: token)
            let added = store.importLive(live)
            status = added > 0 ? "\(added) nuevos · \(store.sponsors.count) en total"
                               : "Al día · \(store.sponsors.count) patrocinadores"
        } catch {
            if case SponsorSync.SyncError.unauthorized = error { auth.lock() }
            status = "No se pudo cargar: \(error.localizedDescription)"
        }
    }

    private func sponsorRow(_ s: Sponsor) -> some View {
        HStack(spacing: 12) {
            logoThumb(s)
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(s.name.isEmpty ? s.slug : s.name).font(.headline)
                    if s.pendingSync {
                        Image(systemName: "arrow.up.circle.fill").font(.caption).foregroundStyle(.orange)
                    }
                }
                Text(s.subtitle).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.caption).foregroundStyle(.tertiary)
        }
    }

    @ViewBuilder private func logoThumb(_ s: Sponsor) -> some View {
        if let d = s.logoData, let ui = UIImage(data: d) {
            Image(uiImage: ui).resizable().scaledToFit().frame(width: 40, height: 40)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 8))
        } else {
            RoundedRectangle(cornerRadius: 8).fill(Color(.secondarySystemBackground))
                .frame(width: 40, height: 40)
                .overlay(Text(String(s.name.isEmpty ? "?" : s.name.prefix(2)).uppercased())
                    .font(.caption.bold()).foregroundStyle(.secondary))
        }
    }
}

// MARK: - Create / edit one sponsor

struct SponsorFormView: View {
    @EnvironmentObject var recorder: LocationRecorder
    @State private var draft: Sponsor
    @State private var photoItem: PhotosPickerItem? = nil
    @State private var editingLoc: SponsorLocation? = nil
    @State private var editingLocIsNew = false
    var onSave: (Sponsor) -> Void
    @Environment(\.dismiss) private var dismiss
    private let isNew: Bool

    init(sponsor: Sponsor?, onSave: @escaping (Sponsor) -> Void) {
        _draft = State(initialValue: sponsor ?? Sponsor())
        self.onSave = onSave
        self.isNew = (sponsor == nil)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Identidad") {
                    TextField("Nombre (ej. Panadería La Flor)", text: $draft.name)
                    HStack {
                        Text("Slug").foregroundStyle(.secondary)
                        Spacer()
                        TextField("se genera del nombre", text: $draft.slug)
                            .autocorrectionDisabled().textInputAutocapitalization(.never)
                            .multilineTextAlignment(.trailing)
                    }
                }
                Section("Logo") { logoRow }
                Section("Contacto") {
                    TextField("Nombre de contacto", text: $draft.contactName)
                    TextField("Correo", text: $draft.contactEmail)
                        .keyboardType(.emailAddress).autocorrectionDisabled().textInputAutocapitalization(.never)
                    TextField("Teléfono", text: $draft.phone).keyboardType(.phonePad)
                }
                Section {
                    Picker("Tipo", selection: $draft.tier) {
                        Text("Intercambio").tag("barter")
                        Text("Pagado").tag("paid")
                    }
                    Toggle("Activo", isOn: $draft.active)
                } footer: {
                    Text(draft.tier == "barter"
                         ? "Intercambio: los pines se publican en el mapa al sincronizar."
                         : "Pagado: los pines se publican cuando existe un contrato firmado (pagos aparte).")
                }
                locationsSection
                Section("Notas") {
                    TextField("Notas internas", text: $draft.notes, axis: .vertical).lineLimit(1...4)
                }
            }
            .navigationTitle(isNew ? "Nuevo patrocinador" : (draft.name.isEmpty ? "Editar" : draft.name))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Guardar") { save() }
                        .disabled(draft.name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onChange(of: photoItem) { _, item in Task { await loadLogo(item) } }
            .sheet(item: $editingLoc) { loc in
                SponsorLocationEditor(loc: loc, isNew: editingLocIsNew) { updated in
                    if let i = draft.locations.firstIndex(where: { $0.id == updated.id }) { draft.locations[i] = updated }
                    else { draft.locations.append(updated) }
                } onDelete: { l in
                    draft.locations.removeAll { $0.id == l.id }
                }
            }
        }
    }

    @ViewBuilder private var logoRow: some View {
        HStack(spacing: 14) {
            if let d = draft.logoData, let ui = UIImage(data: d) {
                Image(uiImage: ui).resizable().scaledToFit().frame(width: 56, height: 56)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            } else {
                RoundedRectangle(cornerRadius: 10).fill(Color(.secondarySystemBackground))
                    .frame(width: 56, height: 56)
                    .overlay(Image(systemName: "photo").foregroundStyle(.secondary))
            }
            VStack(alignment: .leading, spacing: 6) {
                PhotosPicker(selection: $photoItem, matching: .images) {
                    Label(draft.logoData == nil ? "Elegir logo" : "Cambiar logo", systemImage: "photo.on.rectangle")
                }
                if draft.logoData != nil {
                    Button("Quitar logo", role: .destructive) { draft.logoData = nil; photoItem = nil }
                        .font(.footnote)
                }
            }
            Spacer()
        }
    }

    private var locationsSection: some View {
        Section("Ubicaciones (\(draft.locations.count))") {
            ForEach(draft.locations) { loc in
                Button {
                    editingLoc = loc; editingLocIsNew = false
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "mappin.circle.fill").foregroundStyle(loc.active ? .blue : .secondary)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(loc.label.isEmpty ? "Ubicación" : loc.label).foregroundStyle(.primary)
                            Text(String(format: "%.5f, %.5f", loc.lat, loc.lon))
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        if !loc.active { Text("Inactiva").font(.caption2).foregroundStyle(.secondary) }
                    }
                }
                .buttonStyle(.plain)
            }
            .onDelete { idx in draft.locations.remove(atOffsets: idx) }
            Button {
                let c = recorder.current?.coordinate
                editingLoc = SponsorLocation(lat: c?.latitude ?? 18.462, lon: c?.longitude ?? -97.393)
                editingLocIsNew = true
            } label: { Label("Agregar ubicación", systemImage: "plus") }
        }
    }

    private func save() {
        var s = draft
        s.name = s.name.trimmingCharacters(in: .whitespaces)
        s.slug = s.slug.trimmingCharacters(in: .whitespaces).slugified
        if s.slug.isEmpty { s.slug = s.name.slugified }
        onSave(s); dismiss()
    }

    @MainActor private func loadLogo(_ item: PhotosPickerItem?) async {
        guard let item, let data = try? await item.loadTransferable(type: Data.self) else { return }
        draft.logoData = downscaledPNG(data) ?? data
    }
}

// MARK: - Place one location on the map

struct SponsorLocationEditor: View {
    @EnvironmentObject var recorder: LocationRecorder
    @State private var loc: SponsorLocation
    let isNew: Bool
    var onSave: (SponsorLocation) -> Void
    var onDelete: (SponsorLocation) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var camera: MapCameraPosition

    init(loc: SponsorLocation, isNew: Bool,
         onSave: @escaping (SponsorLocation) -> Void,
         onDelete: @escaping (SponsorLocation) -> Void) {
        _loc = State(initialValue: loc)
        self.isNew = isNew
        self.onSave = onSave
        self.onDelete = onDelete
        _camera = State(initialValue: .region(MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: loc.lat, longitude: loc.lon),
            span: MKCoordinateSpan(latitudeDelta: 0.02, longitudeDelta: 0.02))))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                MapReader { proxy in
                    Map(position: $camera) {
                        Marker(loc.label.isEmpty ? "Ubicación" : loc.label, coordinate: loc.coord)
                    }
                    .onTapGesture { pt in
                        if let c = proxy.convert(pt, from: .local) { loc.lat = c.latitude; loc.lon = c.longitude }
                    }
                }
                .frame(maxHeight: .infinity)

                Form {
                    Section {
                        TextField("Etiqueta (ej. Sucursal centro)", text: $loc.label)
                        Toggle("Activa", isOn: $loc.active)
                        Button {
                            if let c = recorder.current?.coordinate {
                                loc.lat = c.latitude; loc.lon = c.longitude
                                camera = .region(MKCoordinateRegion(center: c,
                                    span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)))
                            }
                        } label: { Label("Usar mi ubicación", systemImage: "location.fill") }
                        .disabled(recorder.current == nil)
                    } footer: {
                        Text("Toca el mapa para colocar el pin.  \(String(format: "%.5f, %.5f", loc.lat, loc.lon))")
                    }
                }
                .frame(height: 240)
            }
            .navigationTitle(isNew ? "Nueva ubicación" : "Ubicación")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) { Button("Listo") { onSave(loc); dismiss() } }
                if !isNew {
                    ToolbarItem(placement: .bottomBar) {
                        Button("Borrar ubicación", role: .destructive) { onDelete(loc); dismiss() }
                    }
                }
            }
            .onAppear { recorder.requestAlways() }
        }
    }
}

// MARK: - Push pending sponsors to production

struct SponsorReconcileView: View {
    @EnvironmentObject var store: SponsorStore
    @EnvironmentObject var auth: AdminAuth
    @Environment(\.dismiss) private var dismiss
    @State private var running = false
    @State private var log: [String] = []

    private var pending: [Sponsor] { store.sponsors.filter { $0.pendingSync } }

    var body: some View {
        NavigationStack {
            List {
                Section("\(pending.count) por subir") {
                    if pending.isEmpty {
                        Text("Todo sincronizado con producción").foregroundStyle(.secondary)
                    } else {
                        ForEach(pending) { s in
                            VStack(alignment: .leading, spacing: 2) {
                                Text(s.name.isEmpty ? s.slug : s.name).font(.headline)
                                Text("\(s.locations.count) ubicaciones · \(s.tier == "barter" ? "intercambio" : "pagado")")
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
        for s in pending {
            do {
                try await SponsorSync.push(s, token: token)
                store.markSynced(s.id)
                log.append("✓ \(s.name.isEmpty ? s.slug : s.name)")
            } catch {
                log.append("✗ \(s.name.isEmpty ? s.slug : s.name): \(error.localizedDescription)")
                if case SponsorSync.SyncError.unauthorized = error { auth.lock() }
            }
        }
        running = false
    }
}

// MARK: - helpers

/// Shrink a picked image to a small square-ish PNG so logos stay tiny in D1 and on
/// the wire (they're rendered at ~40–56pt). Returns nil if the data isn't an image.
private func downscaledPNG(_ data: Data, maxDim: CGFloat = 240) -> Data? {
    guard let img = UIImage(data: data) else { return nil }
    let w = img.size.width, h = img.size.height
    guard w > 0, h > 0 else { return nil }
    let scale = min(1, maxDim / max(w, h))
    let size = CGSize(width: w * scale, height: h * scale)
    let fmt = UIGraphicsImageRendererFormat.default(); fmt.scale = 1
    return UIGraphicsImageRenderer(size: size, format: fmt)
        .image { _ in img.draw(in: CGRect(origin: .zero, size: size)) }
        .pngData()
}
