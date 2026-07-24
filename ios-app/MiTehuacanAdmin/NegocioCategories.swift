import Foundation

/// The directory's category taxonomy — kept in sync with the public intake form
/// (`src/app/directorio/alta.html`). Value = the stored slug; label = what the
/// admin sees. Grouped so the picker mirrors the web dropdown.
enum NegocioCategories {
    struct Group: Identifiable { let name: String; let items: [Item]; var id: String { name } }
    struct Item: Identifiable, Hashable { let value: String; let label: String; var id: String { value } }

    static let groups: [Group] = [
        Group(name: "Fiestas y eventos", items: [
            Item(value: "taquiza", label: "Taquiza / Catering / Banquetes"),
            Item(value: "pastel", label: "Pastel y repostería"),
            Item(value: "dj", label: "DJ y sonido"),
            Item(value: "mariachi", label: "Mariachi / música en vivo"),
            Item(value: "foto-video", label: "Foto y video"),
            Item(value: "decoracion", label: "Decoración y globos"),
            Item(value: "mobiliario", label: "Mobiliario, carpas y sillas"),
            Item(value: "salon", label: "Salón de eventos / jardín"),
            Item(value: "meseros", label: "Meseros y staff"),
            Item(value: "flores", label: "Flores y arreglos"),
            Item(value: "brincolines", label: "Brincolines e inflables"),
            Item(value: "pinatas", label: "Piñatas y dulces"),
            Item(value: "vajilla", label: "Renta de vajilla / menaje"),
            Item(value: "bar-movil", label: "Bar móvil / cocteles"),
            Item(value: "animacion", label: "Animación / payasos / botargas"),
            Item(value: "seguridad-eventos", label: "Seguridad para eventos"),
            Item(value: "invitaciones", label: "Invitaciones y papelería"),
        ]),
        Group(name: "Comida", items: [
            Item(value: "restaurante", label: "Restaurante"),
            Item(value: "fonda", label: "Fonda / cocina económica"),
            Item(value: "antojitos", label: "Antojitos / garnachas"),
            Item(value: "cafeteria", label: "Cafetería"),
            Item(value: "panaderia", label: "Panadería"),
            Item(value: "tortilleria", label: "Tortillería"),
            Item(value: "marisqueria", label: "Marisquería"),
            Item(value: "pizzeria", label: "Pizzería"),
            Item(value: "foodtruck", label: "Food truck"),
            Item(value: "dulceria", label: "Dulcería"),
        ]),
        Group(name: "Salud y belleza", items: [
            Item(value: "medico", label: "Médico / consultorio"),
            Item(value: "dentista", label: "Dentista"),
            Item(value: "farmacia", label: "Farmacia"),
            Item(value: "optica", label: "Óptica"),
            Item(value: "veterinaria", label: "Veterinaria"),
            Item(value: "estetica", label: "Estética / salón de belleza"),
            Item(value: "barberia", label: "Barbería"),
            Item(value: "unas", label: "Uñas"),
            Item(value: "spa", label: "Spa / masajes"),
            Item(value: "gimnasio", label: "Gimnasio"),
        ]),
        Group(name: "Servicios para el hogar", items: [
            Item(value: "plomero", label: "Plomero"),
            Item(value: "electricista", label: "Electricista"),
            Item(value: "albanil", label: "Albañil / construcción"),
            Item(value: "carpintero", label: "Carpintero"),
            Item(value: "herrero", label: "Herrero"),
            Item(value: "pintor", label: "Pintor"),
            Item(value: "jardineria", label: "Jardinería"),
            Item(value: "limpieza", label: "Limpieza / servicio doméstico"),
            Item(value: "fumigacion", label: "Fumigación"),
            Item(value: "clima", label: "Aire acondicionado / refrigeración"),
            Item(value: "cerrajero", label: "Cerrajero"),
        ]),
        Group(name: "Autos y transporte", items: [
            Item(value: "taller", label: "Taller mecánico"),
            Item(value: "refaccionaria", label: "Refaccionaria"),
            Item(value: "vulcanizadora", label: "Vulcanizadora"),
            Item(value: "autolavado", label: "Autolavado"),
            Item(value: "hojalateria", label: "Hojalatería y pintura"),
            Item(value: "grua", label: "Grúa"),
            Item(value: "fletes", label: "Mudanzas / fletes"),
            Item(value: "renta-autos", label: "Renta de autos"),
        ]),
        Group(name: "Tiendas y comercio", items: [
            Item(value: "abarrotes", label: "Abarrotes / tienda"),
            Item(value: "ferreteria", label: "Ferretería"),
            Item(value: "papeleria", label: "Papelería"),
            Item(value: "ropa", label: "Ropa y boutique"),
            Item(value: "zapateria", label: "Zapatería"),
            Item(value: "muebleria", label: "Mueblería"),
            Item(value: "electronica", label: "Electrónica / celulares"),
            Item(value: "regalos", label: "Regalos y novedades"),
            Item(value: "florateria", label: "Florería"),
            Item(value: "licores", label: "Vinos y licores"),
        ]),
        Group(name: "Profesionales", items: [
            Item(value: "abogado", label: "Abogado"),
            Item(value: "contador", label: "Contador"),
            Item(value: "arquitecto", label: "Arquitecto / ingeniero"),
            Item(value: "inmobiliaria", label: "Inmobiliaria / bienes raíces"),
            Item(value: "notaria", label: "Notaría"),
            Item(value: "viajes", label: "Agencia de viajes"),
            Item(value: "imprenta", label: "Diseño / publicidad / imprenta"),
            Item(value: "clases", label: "Clases / tutorías"),
            Item(value: "escuela", label: "Escuela / academia"),
            Item(value: "seguros", label: "Seguros"),
        ]),
        Group(name: "Otros servicios", items: [
            Item(value: "hotel", label: "Hotel / hospedaje"),
            Item(value: "lavanderia", label: "Lavandería / tintorería"),
            Item(value: "estudio-foto", label: "Estudio fotográfico"),
            Item(value: "funeraria", label: "Funeraria"),
            Item(value: "otro", label: "Otro (escribir)"),
        ]),
    ]

    /// Human label for a stored slug (falls back to the slug itself).
    static func label(for value: String) -> String {
        for g in groups { for i in g.items where i.value == value { return i.label } }
        return value.isEmpty ? "Elige una categoría" : value
    }
}
