import SwiftUI

/// Editor for one stop: name, kind (origen / parada mayor / última), and the
/// schedule you enter by hand on the combi — intervals + first/last departure
/// for weekday, Saturday, and Sunday.
struct StopEditView: View {
    @State var stop: Stop
    var onSave: (Stop) -> Void
    var onDelete: (Stop) -> Void
    @Environment(\.dismiss) private var dismiss
    private var isExisting: Bool

    init(stop: Stop, onSave: @escaping (Stop) -> Void, onDelete: @escaping (Stop) -> Void) {
        _stop = State(initialValue: stop)
        self.onSave = onSave
        self.onDelete = onDelete
        self.isExisting = stop.name.isEmpty == false
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Parada") {
                    TextField("Nombre (ej. Terminal centro)", text: $stop.name)
                    Picker("Tipo", selection: $stop.kind) {
                        ForEach(StopKind.allCases, id: \.self) { Text($0.label).tag($0) }
                    }
                }
                daySection("Lunes a viernes", $stop.schedule.weekday)
                daySection("Sábado", $stop.schedule.saturday)
                daySection("Domingo", $stop.schedule.sunday)
            }
            .navigationTitle("Horario de parada")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Guardar") { onSave(stop); dismiss() }.disabled(stop.name.isEmpty)
                }
                if isExisting {
                    ToolbarItem(placement: .bottomBar) {
                        Button("Borrar parada", role: .destructive) { onDelete(stop); dismiss() }
                    }
                }
            }
        }
    }

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
