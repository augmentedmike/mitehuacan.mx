import SwiftUI
import MapKit

/// The "Negocios" section: the review queue for self-registered businesses, plus a
/// "+" to add one by hand. Listings publish on submit, so this is review-after-the-fact:
///   • Aprobar  — clears it from the queue; it stays live in the directory.
///   • Rechazar — hides it (goes dark) and clears it from the queue.
///   • +        — admin enters a business; it goes live pre-approved (skips the queue).
struct NegocioListView: View {
    @EnvironmentObject var store: NegocioStore
    @EnvironmentObject var auth: AdminAuth
    @State private var showUnlock = false
    @State private var confirmReject: Negocio? = nil
    @State private var showAdd = false
    @State private var addedName = ""

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
                        VStack(spacing: 10) {
                            Button { showAdd = true } label: {
                                Label("Agregar negocio", systemImage: "plus")
                            }
                            .buttonStyle(.borderedProminent)
                            Button { Task { await reload() } } label: {
                                Label("Actualizar", systemImage: "arrow.clockwise")
                            }
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
                    Button { showAdd = true } label: { Image(systemName: "plus") }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { Task { await reload() } } label: { Image(systemName: "arrow.clockwise") }
                        .disabled(store.loading)
                }
            }
            .overlay(alignment: .top) {
                if !addedName.isEmpty {
                    Text("“\(addedName)” se publicó en el directorio.")
                        .font(.footnote).padding(.horizontal, 14).padding(.vertical, 10)
                        .background(.green.opacity(0.9), in: Capsule()).foregroundStyle(.white)
                        .padding(.top, 8).shadow(radius: 4)
                        .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
            .task { await reload() }
            .sheet(isPresented: $showAdd) {
                NegocioFormView { draft in await add(draft) }
            }
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

    /// Save an admin-entered business. Returns an error string to the form (nil =
    /// success, which dismisses the sheet and flashes a confirmation banner).
    private func add(_ draft: NegocioDraft) async -> String? {
        guard let token = auth.token else { showUnlock = true; return "Sesión bloqueada" }
        let err = await store.create(draft, token: token)
        if err == "unauthorized" { auth.lock(); showUnlock = true; return "Sesión inválida" }
        if let err { return err }
        withAnimation { addedName = draft.name.trimmingCharacters(in: .whitespaces) }
        Task {   // auto-dismiss the banner
            try? await Task.sleep(nanoseconds: 3_500_000_000)
            withAnimation { addedName = "" }
        }
        return nil
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

// MARK: - Add a business by hand

/// The admin "+" form. Collects the same fields a business would self-register, plus
/// an optional map pin. On save it PUTs to /api/admin/negocios (live + pre-approved).
struct NegocioFormView: View {
    @EnvironmentObject var recorder: LocationRecorder
    @State private var draft = NegocioDraft()
    @State private var error = ""
    @State private var saving = false
    /// Returns an error string, or nil on success (which dismisses the sheet).
    var onSave: (NegocioDraft) async -> String?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Negocio") {
                    TextField("Nombre (ej. Taquería El Güero)", text: $draft.name)
                    NavigationLink {
                        NegocioCategoryPicker(selection: $draft.category)
                    } label: {
                        HStack {
                            Text("Categoría")
                            Spacer()
                            Text(draft.category.isEmpty ? "Elegir" : NegocioCategories.label(for: draft.category))
                                .foregroundStyle(draft.category.isEmpty ? .secondary : .primary)
                        }
                    }
                    NavigationLink {
                        NegocioCategoryPicker(selection: $draft.category2, allowNone: true)
                    } label: {
                        HStack {
                            Text("2ª categoría").foregroundStyle(.secondary)
                            Spacer()
                            Text(draft.category2.isEmpty ? "Opcional" : NegocioCategories.label(for: draft.category2))
                                .foregroundStyle(draft.category2.isEmpty ? .secondary : .primary)
                        }
                    }
                    if draft.category == "otro" || draft.category2 == "otro" {
                        TextField("¿A qué se dedica? (categoría libre)", text: $draft.categoryOther)
                    }
                    TextField("¿Qué ofrece? (opcional)", text: $draft.description, axis: .vertical)
                        .lineLimit(1...4)
                }

                Section("Contacto") {
                    TextField("WhatsApp (10 dígitos)", text: $draft.whatsapp).keyboardType(.numberPad)
                    TextField("Teléfono (opcional)", text: $draft.phone).keyboardType(.numberPad)
                    TextField("Nombre del dueño (opcional)", text: $draft.ownerName)
                    TextField("Correo (opcional)", text: $draft.email)
                        .keyboardType(.emailAddress).autocorrectionDisabled().textInputAutocapitalization(.never)
                }

                Section("Presencia (opcional)") {
                    TextField("Sitio web", text: $draft.website)
                        .autocorrectionDisabled().textInputAutocapitalization(.never)
                    TextField("Facebook", text: $draft.facebook)
                        .autocorrectionDisabled().textInputAutocapitalization(.never)
                    TextField("Instagram", text: $draft.instagram)
                        .autocorrectionDisabled().textInputAutocapitalization(.never)
                }

                Section("Horario y precios (opcional)") {
                    TextField("Horario (ej. Lun–Sáb 9–7)", text: $draft.hours)
                    TextField("Precio desde ($)", text: $draft.priceFrom).keyboardType(.decimalPad)
                    TextField("Nota de precio (ej. por evento)", text: $draft.priceNote)
                    TextField("Zona de servicio (ej. Todo Tehuacán)", text: $draft.serviceArea)
                }

                locationSection

                if !error.isEmpty {
                    Section { Text(error).foregroundStyle(.red).font(.footnote) }
                }
            }
            .navigationTitle("Nuevo negocio")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Guardar") { save() }
                        .disabled(!draft.canSave || saving)
                }
            }
            .onAppear { recorder.requestAlways() }
        }
    }

    @ViewBuilder private var locationSection: some View {
        Section {
            Toggle("Tiene local físico", isOn: $draft.hasLocation.animation())
            if draft.hasLocation {
                TextField("Dirección (opcional)", text: $draft.address)
                TextField("Colonia (opcional)", text: $draft.colonia)
                NegocioPinMap(lat: $draft.lat, lon: $draft.lon)
                    .frame(height: 260)
                    .listRowInsets(EdgeInsets())
                Button {
                    if let c = recorder.current?.coordinate { draft.lat = c.latitude; draft.lon = c.longitude }
                } label: { Label("Usar mi ubicación", systemImage: "location.fill") }
                    .disabled(recorder.current == nil)
                Text(String(format: "Pin: %.5f, %.5f", draft.lat, draft.lon))
                    .font(.caption).foregroundStyle(.secondary)
            }
        } header: {
            Text("Ubicación")
        } footer: {
            Text(draft.hasLocation
                 ? "Toca el mapa para colocar el pin donde está el local."
                 : "Sin local (plomero, DJ, servicio a domicilio): aparece por zona de servicio, sin pin.")
        }
    }

    private func save() {
        saving = true; error = ""
        Task {
            if let err = await onSave(draft) { error = err; saving = false }
            else { dismiss() }
        }
    }
}

/// Grouped category chooser (mirrors the web dropdown). Sets the binding and pops.
private struct NegocioCategoryPicker: View {
    @Binding var selection: String
    var allowNone: Bool = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        List {
            if allowNone {
                Button { selection = ""; dismiss() } label: {
                    row(label: "Ninguna", value: "", isNone: true)
                }
            }
            ForEach(NegocioCategories.groups) { g in
                Section(g.name) {
                    ForEach(g.items) { item in
                        Button { selection = item.value; dismiss() } label: {
                            row(label: item.label, value: item.value)
                        }
                    }
                }
            }
        }
        .navigationTitle("Categoría")
        .navigationBarTitleDisplayMode(.inline)
    }

    @ViewBuilder private func row(label: String, value: String, isNone: Bool = false) -> some View {
        HStack {
            Text(label).foregroundStyle(isNone ? .secondary : .primary)
            Spacer()
            if selection == value { Image(systemName: "checkmark").foregroundStyle(.blue) }
        }
    }
}

/// A tap-to-place pin on a map, bound to a lat/lon. Same interaction as the sponsor
/// location editor: tap anywhere to move the pin; "use my location" is offered above.
private struct NegocioPinMap: View {
    @Binding var lat: Double
    @Binding var lon: Double
    @State private var camera: MapCameraPosition

    init(lat: Binding<Double>, lon: Binding<Double>) {
        _lat = lat; _lon = lon
        _camera = State(initialValue: .region(MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: lat.wrappedValue, longitude: lon.wrappedValue),
            span: MKCoordinateSpan(latitudeDelta: 0.02, longitudeDelta: 0.02))))
    }

    var body: some View {
        MapReader { proxy in
            Map(position: $camera) {
                Marker("Negocio", coordinate: CLLocationCoordinate2D(latitude: lat, longitude: lon))
            }
            .onTapGesture { pt in
                if let c = proxy.convert(pt, from: .local) { lat = c.latitude; lon = c.longitude }
            }
            // Recenter only on a big jump (e.g. "use my location"), not small map taps.
            .onChange(of: lat) { old, new in recenterIfFar(dLat: abs(new - old)) }
            .onChange(of: lon) { old, new in recenterIfFar(dLon: abs(new - old)) }
        }
    }

    private func recenterIfFar(dLat: Double = 0, dLon: Double = 0) {
        if dLat > 0.01 || dLon > 0.01 {
            camera = .region(MKCoordinateRegion(
                center: CLLocationCoordinate2D(latitude: lat, longitude: lon),
                span: MKCoordinateSpan(latitudeDelta: 0.02, longitudeDelta: 0.02)))
        }
    }
}
