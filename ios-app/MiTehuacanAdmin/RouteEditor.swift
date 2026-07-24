import SwiftUI
import MapKit

// MARK: - Home: list of routes + "new route"

struct RouteListView: View {
    @EnvironmentObject var store: RouteStore
    @EnvironmentObject var auth: AdminAuth
    @State private var path: [Route.ID] = []
    @State private var showForm = false
    @State private var loading = false
    @State private var status = ""
    @State private var showUnlock = false
    @State private var showReconcile = false
    @State private var query = ""
    @State private var filter = "all"          // "all" | "pending" | <kind>

    private var kinds: [String] {
        Array(Set(store.routes.compactMap { $0.kind }).filter { !$0.isEmpty }).sorted()
    }
    private var filtered: [Route] {
        store.routes.filter { r in
            let byFilter = filter == "all"
                || (filter == "pending" && r.pendingSync)
                || (r.kind ?? "") == filter
            let byQuery = query.isEmpty
                || [r.name, r.lineName, r.origin, r.destination]
                    .contains { $0.localizedCaseInsensitiveContains(query) }
            return byFilter && byQuery
        }
    }

    var liveCount: Int { store.routes.filter { $0.serverId != nil }.count }

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if store.routes.isEmpty {
                    ContentUnavailableView {
                        Label(loading ? "Cargando rutas…" : "Sin rutas todavía", systemImage: "bus")
                    } description: {
                        Text(loading ? "Descargando las rutas en vivo de mitehuacan.mx"
                                     : "Carga las rutas en vivo para editarlas y depurarlas, o toca + para grabar una nueva.")
                    } actions: {
                        if !loading {
                            Button { Task { await sync() } } label: { Label("Cargar rutas en vivo", systemImage: "arrow.down.circle") }
                                .buttonStyle(.borderedProminent)
                        } else { ProgressView() }
                    }
                } else {
                    VStack(spacing: 0) {
                        VStack(spacing: 8) {
                            TextField("Buscar ruta, número o colonia", text: $query)
                                .textFieldStyle(.roundedBorder)
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    chip("Todas", "all")
                                    if store.pendingCount > 0 { chip("Por subir (\(store.pendingCount))", "pending") }
                                    ForEach(kinds, id: \.self) { k in chip(k.capitalized, k) }
                                }
                            }
                            .frame(height: 34)
                            if loading {
                                HStack(spacing: 6) {
                                    ProgressView().controlSize(.small)
                                    Text("Actualizando rutas…").font(.caption).foregroundStyle(.secondary)
                                    Spacer()
                                }
                            }
                        }
                        .padding(.horizontal, 12).padding(.top, 8).padding(.bottom, 6)
                        .background(.bar)

                        List {
                            ForEach(filtered) { r in
                                NavigationLink(value: r.id) { routeRow(r) }
                            }
                            .onDelete { idx in idx.map { filtered[$0] }.forEach(store.delete) }
                            if filtered.isEmpty {
                                Text("Ninguna ruta coincide").foregroundStyle(.secondary)
                            } else if !status.isEmpty {
                                Text(status).font(.footnote).foregroundStyle(.secondary)
                            }
                        }
                        .listStyle(.plain)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) { SectionTitle() }
                ToolbarItem(placement: .topBarLeading) {
                    Button { Task { await sync() } } label: {
                        if loading { ProgressView() } else { Label("Cargar rutas", systemImage: "arrow.down.circle") }
                    }.disabled(loading)
                }
                ToolbarItem(placement: .primaryAction) {
                    Button { showForm = true } label: { Label("Nueva ruta", systemImage: "plus") }
                }
                if store.pendingCount > 0 {
                    ToolbarItem(placement: .bottomBar) {
                        Button {
                            if auth.unlocked { showReconcile = true } else { showUnlock = true }
                        } label: {
                            Label("\(store.pendingCount) por subir · Reconciliar", systemImage: "arrow.up.circle.fill")
                        }.tint(.orange)
                    }
                }
            }
            .navigationDestination(for: Route.ID.self) { id in RouteDetailView(routeID: id) }
            .sheet(isPresented: $showForm) {
                RouteFormView(route: nil) { newRoute in
                    store.add(newRoute)
                    showForm = false
                    path.append(newRoute.id)      // drop straight into the record screen
                }
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
            }
            .sheet(isPresented: $showUnlock) { UnlockView { showReconcile = true } }
            .sheet(isPresented: $showReconcile) { ReconcileView() }
            .task { await bootstrap() }   // preload bundled routes, then refresh live
        }
    }

    // First open: load the routes bundled in the app instantly (offline), then
    // try to refresh from live. The app is never empty even with no signal.
    @MainActor
    private func bootstrap() async {
        if store.routes.isEmpty {
            let seed = RouteSync.loadBundled()
            if !seed.isEmpty { store.importLive(seed); status = "\(seed.count) rutas cargadas" }
        }
        await sync()
    }

    @MainActor
    private func sync() async {
        guard !loading else { return }
        loading = true
        do {
            let live = try await RouteSync.fetchLive()
            let added = store.importLive(live)
            status = added > 0 ? "\(added) rutas nuevas · \(liveCount) rutas en total"
                               : "Al día · \(liveCount) rutas"
        } catch {
            status = store.routes.isEmpty ? "Error: \(error.localizedDescription)"
                                          : "Sin conexión · \(liveCount) rutas cargadas"
        }
        loading = false
    }

    private func chip(_ label: String, _ value: String) -> some View {
        Button { filter = value } label: {
            Text(label)
                .font(.subheadline.weight(.medium))
                .padding(.horizontal, 13).padding(.vertical, 6)
                .background(filter == value ? Color.accentColor : Color(.secondarySystemBackground), in: Capsule())
                .foregroundStyle(filter == value ? Color.white : Color.primary)
        }
        .buttonStyle(.plain)
    }

    private func routeRow(_ r: Route) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(r.name).font(.headline)
            if !r.subtitle.isEmpty {
                Text(r.subtitle).font(.subheadline).foregroundStyle(.secondary)
            }
            Text("\(r.segments.count) tramos · \(String(format: "%.1f km", r.km)) · \(r.stops.count) paradas")
                .font(.caption).foregroundStyle(.tertiary)
        }
    }
}

extension Route {
    var subtitle: String {
        var parts: [String] = []
        if !lineName.isEmpty { parts.append(lineName) }
        let od = [origin, destination].filter { !$0.isEmpty }.joined(separator: " → ")
        if !od.isEmpty { parts.append(od) }
        return parts.joined(separator: " · ")
    }
}

// MARK: - Form: combi info (create or edit)

struct RouteFormView: View {
    @State var draft: Route
    var onSave: (Route) -> Void
    @Environment(\.dismiss) private var dismiss
    private let isNew: Bool

    init(route: Route?, onSave: @escaping (Route) -> Void) {
        _draft = State(initialValue: route ?? Route(name: ""))
        self.onSave = onSave
        self.isNew = (route == nil)
    }

    private var kindOptions: [String] {
        var s = ["local", "foránea", "urbana", "mixta"]
        if let k = draft.kind, !k.isEmpty, !s.contains(k) { s.insert(k, at: 0) }
        return s
    }
    private var kindBinding: Binding<String> {
        Binding(get: { draft.kind ?? "local" }, set: { draft.kind = $0 })
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Información") {
                    TextField("Nombre (ej. 23 - San Isidro)", text: $draft.name)
                    TextField("Origen", text: $draft.origin)
                    TextField("Destino", text: $draft.destination)
                    Picker("Tipo", selection: kindBinding) {
                        ForEach(kindOptions, id: \.self) { Text($0.capitalized).tag($0) }
                    }
                }
                Section {
                    HStack {
                        Text("Costo por tramo")
                        Spacer()
                        TextField("0", value: $draft.fare, format: .number)
                            .keyboardType(.numberPad).multilineTextAlignment(.trailing).frame(width: 70)
                        Text("MXN").foregroundStyle(.secondary)
                    }
                } footer: {
                    Text("El costo foráneo/intercity depende de las ciudades que se recorren.")
                }
                daySection("Lunes a viernes", $draft.schedule.weekday)
                daySection("Sábado", $draft.schedule.saturday)
                daySection("Domingo", $draft.schedule.sunday)
            }
            .navigationTitle(isNew ? "Nueva ruta" : draft.name.isEmpty ? "Editar ruta" : draft.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isNew ? "Crear y grabar" : "Guardar") { onSave(draft); dismiss() }
                        .disabled(draft.name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }

    // one day-type's schedule: first departure, last departure, interval (min between combis)
    private func daySection(_ title: String, _ day: Binding<DaySchedule>) -> some View {
        Section(title) {
            HStack {
                Text("Primera")
                Spacer()
                TextField("06:00", text: day.first).multilineTextAlignment(.trailing)
                    .keyboardType(.numbersAndPunctuation).frame(width: 90)
            }
            HStack {
                Text("Última")
                Spacer()
                TextField("22:00", text: day.last).multilineTextAlignment(.trailing)
                    .keyboardType(.numbersAndPunctuation).frame(width: 90)
            }
            Stepper("Cada \(day.wrappedValue.intervalMin) min", value: day.intervalMin, in: 0...120, step: 5)
        }
    }
}

// MARK: - Route screen: map + record segments + edit

struct RouteDetailView: View {
    @EnvironmentObject var store: RouteStore
    @EnvironmentObject var recorder: LocationRecorder
    let routeID: Route.ID

    @State private var camera: MapCameraPosition = .userLocation(fallback: .automatic)
    @State private var mode: Mode = .view
    @State private var editingStop: Stop? = nil
    @State private var snipSegment = 0
    @State private var snipLo = 0.0
    @State private var snipHi = 1.0
    @State private var showJoin = false
    @State private var showEditInfo = false

    enum Mode { case view, addStop, snip }

    private var route: Route { store.routes.first(where: { $0.id == routeID }) ?? Route() }

    var body: some View {
        VStack(spacing: 0) {
            mapView
            if recorder.recording { recordingBar } else { editBar }
        }
        .navigationTitle(route.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showEditInfo = true } label: { Image(systemName: "info.circle") }
                    .disabled(recorder.recording)
            }
        }
        .sheet(isPresented: $showEditInfo) {
            RouteFormView(route: route) { updated in store.update(updated) }
                .presentationDetents([.medium, .large])          // reduce / maximize
                .presentationDragIndicator(.visible)             // the handle
                .presentationBackgroundInteraction(.enabled(upThrough: .large))  // map stays live under it
        }
        .sheet(item: $editingStop) { stop in
            StopEditView(stop: stop) { updated in
                var r = route
                if let i = r.stops.firstIndex(where: { $0.id == updated.id }) { r.stops[i] = updated }
                else { r.stops.append(updated) }
                store.update(r)
            } onDelete: { s in
                var r = route; r.stops.removeAll { $0.id == s.id }; store.update(r)
            }
        }
        .confirmationDialog("Unir con otra ruta", isPresented: $showJoin) {
            ForEach(store.routes.filter { $0.id != routeID }) { other in
                Button(other.name) { store.merge(other, into: routeID) }
            }
        } message: { Text("Los tramos de la otra ruta se agregan a esta.") }
        .onAppear { recorder.requestAlways(); fitCamera() }
    }

    // MARK: map

    private var mapView: some View {
        MapReader { proxy in
            Map(position: $camera) {
                UserAnnotation()
                // saved (aggregated) segments
                ForEach(Array(route.segments.enumerated()), id: \.offset) { i, seg in
                    if seg.count > 1 {
                        MapPolyline(coordinates: seg.map(\.coord))
                            .stroke(i == snipSegment && mode == .snip ? .orange : .pink, lineWidth: 4)
                    }
                }
                // live snip preview
                if mode == .snip, let seg = route.segments[safe: snipSegment], seg.count > 1 {
                    let lo = Int(snipLo * Double(seg.count - 1)), hi = Int(snipHi * Double(seg.count - 1))
                    if lo < hi {
                        MapPolyline(coordinates: Array(seg[lo...hi]).map(\.coord)).stroke(.green, lineWidth: 6)
                    }
                }
                // live track while recording a new tramo
                if recorder.recording, recorder.points.count > 1 {
                    MapPolyline(coordinates: recorder.points.map(\.coord)).stroke(.red, lineWidth: 5)
                }
                ForEach(route.stops) { s in
                    Annotation(s.name.isEmpty ? s.kind.label : s.name, coordinate: s.coord) {
                        Image(systemName: s.kind == .origin ? "flag.fill" : s.kind == .last ? "flag.checkered" : "mappin.circle.fill")
                            .foregroundStyle(s.kind == .major ? .blue : .purple)
                    }
                }
            }
            .onTapGesture { pt in
                guard mode == .addStop, !recorder.recording, let coord = proxy.convert(pt, from: .local) else { return }
                editingStop = Stop(lat: coord.latitude, lon: coord.longitude)
                mode = .view
            }
        }
        .frame(maxHeight: .infinity)
    }

    // MARK: recording bar

    private var recordingBar: some View {
        VStack(spacing: 10) {
            HStack(spacing: 12) {
                Circle().fill(.red).frame(width: 10, height: 10).symbolEffect(.pulse)
                Text("Grabando tramo").font(.headline)
                Spacer()
                Text("\(recorder.points.count) pts · \(String(format: "%.1f km", recorder.points.km))")
                    .font(.subheadline).monospacedDigit().foregroundStyle(.secondary)
            }
            Text("Mantén la app abierta o bloquea la pantalla — sigue grabando.")
                .font(.caption2).foregroundStyle(.secondary).frame(maxWidth: .infinity, alignment: .leading)
            Button {
                let ride = recorder.stop()
                if ride.count > 1 { store.appendRide(ride, to: routeID) }   // aggregate into this route
                fitCamera()
            } label: {
                Label("Detener y guardar tramo", systemImage: "stop.fill")
                    .font(.title3.bold()).frame(maxWidth: .infinity).padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent).tint(.red)
        }
        .padding()
        .background(.regularMaterial)
    }

    // MARK: edit bar (not recording)

    private var editBar: some View {
        VStack(spacing: 10) {
            if mode == .snip { snipControls }

            Button {
                recorder.start()
                mode = .view
            } label: {
                Label(route.segments.isEmpty ? "Grabar tramo" : "Grabar otro tramo", systemImage: "record.circle")
                    .font(.title3.bold()).frame(maxWidth: .infinity).padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent).tint(.pink)
            .disabled(!recorder.authorized)

            HStack(spacing: 10) {
                modeButton("Parada", "mappin.and.ellipse", .addStop)
                modeButton("Recortar", "scissors", .snip).disabled(route.segments.isEmpty)
                Button { showJoin = true } label: { chip("Unir", "arrow.triangle.merge") }
                    .disabled(store.routes.count < 2)
            }

            HStack {
                Text("\(route.segments.count) tramos · \(route.pointCount) pts · \(route.stops.count) paradas")
                    .font(.caption).foregroundStyle(.secondary)
                Spacer()
                if !route.segments.isEmpty {
                    Menu {
                        ForEach(Array(route.segments.enumerated()), id: \.offset) { i, _ in
                            Button("Borrar tramo \(i + 1)", role: .destructive) { store.deleteSegment(routeID: routeID, segment: i) }
                        }
                    } label: { Image(systemName: "trash") }
                }
            }
        }
        .padding()
        .background(.regularMaterial)
    }

    private var snipControls: some View {
        VStack(spacing: 6) {
            if route.segments.count > 1 {
                Picker("Tramo", selection: $snipSegment) {
                    ForEach(0..<route.segments.count, id: \.self) { Text("Tramo \($0 + 1)").tag($0) }
                }.pickerStyle(.segmented)
            }
            HStack { Text("Inicio"); Slider(value: $snipLo, in: 0...1) }
            HStack { Text("Fin   "); Slider(value: $snipHi, in: 0...1) }
            Button("Recortar a la parte verde") {
                if let seg = route.segments[safe: snipSegment] {
                    let lo = Int(snipLo * Double(seg.count - 1)), hi = Int(snipHi * Double(seg.count - 1))
                    store.snip(routeID: routeID, segment: snipSegment, keep: min(lo, hi)...max(lo, hi))
                }
                mode = .view
            }.buttonStyle(.bordered)
        }
    }

    private func modeButton(_ t: String, _ icon: String, _ m: Mode) -> some View {
        Button { mode = (mode == m ? .view : m) } label: { chip(t, icon) }
            .tint(mode == m ? .accentColor : .secondary)
    }
    private func chip(_ t: String, _ icon: String) -> some View {
        Label(t, systemImage: icon).frame(maxWidth: .infinity).padding(.vertical, 8)
            .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))
    }

    private func fitCamera() {
        let pts = route.line.map(\.coord)
        guard !pts.isEmpty else { return }
        let lats = pts.map(\.latitude), lons = pts.map(\.longitude)
        let c = CLLocationCoordinate2D(latitude: (lats.min()! + lats.max()!) / 2, longitude: (lons.min()! + lons.max()!) / 2)
        let span = MKCoordinateSpan(latitudeDelta: max(0.01, (lats.max()! - lats.min()!) * 1.4),
                                    longitudeDelta: max(0.01, (lons.max()! - lons.min()!) * 1.4))
        camera = .region(MKCoordinateRegion(center: c, span: span))
    }
}

extension Array { subscript(safe i: Int) -> Element? { indices.contains(i) ? self[i] : nil } }
