/** @odoo-module **/

import { Component, useState, useRef, onMounted   } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class Seguimiento extends Component {
    setup() {
    super.setup();
    const http = useService("http");
    this.state = useState({
        items: [],
        text: "",
    });

    this.textFuncion = async (ev, itemId) => {
        const value = ev.target.value;
        const row = this.state.items.find(item => item.id === itemId);

        if (row) {
            // Actualiza el estado local
            row.notes = value;
            console.log(itemId);

            // Guardar el cambio
            const writeBody = {
                jsonrpc: "2.0",
                method: "call",
                params: {
                    model: "dtm.odt",
                    method: "write",
                    args: [
                      [itemId],            // IDs de los registros a actualizar
                      { notes: value }     // Datos a actualizar
                    ],
                    kwargs: {}             // Argumentos opcionales (vacío si no necesitas nada más)
                },
                id: Math.floor(Math.random() * 1000),
            };

            try {
                const writeResponse = await fetch("/web/dataset/call_kw", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(writeBody),
                    credentials: "include",
                });
                const writeData = await writeResponse.json();
                console.log("✅ Guardado en Odoo:", writeData);
            } catch (error) {
                console.error("❌ Error al guardar en Odoo:", error);
            }
        } else {
            console.warn("⚠️ No se encontró el item con id:", itemId);
        }
};


    onMounted(async () => {

        // Autenticación
        const body = {
          jsonrpc: "2.0",
          method: "call",
          params: {
            service: "common",
            method: "authenticate",
            args: ["backup", "rafaguzmang@hotmail.com", "admin", {}], // Contraseña
          },
          id: Math.floor(Math.random() * 1000),
        };

        try {
          const response = await fetch("/jsonrpc", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            credentials: "include", // Muy importante para mantener la sesión
          });
          const data = await response.json();
//          console.log("🔐 Data:", data.result);
        } catch (error) {
          console.error("❌ Error al obtener datos:", error);
        }

        // Obtener datos para la tabla
        const readBody = {
          jsonrpc: "2.0",
          method: "call",
          params: {
            model: "dtm.odt",
            method: "search_read",
            args: [
              ['|',['manufactura','=',false],['nesteo_chk','=',true]], // Dominio (puedes ajustar)
              [
                'id',
                'od_number',
                'firma_ventas',
                'version_ot',
                'date_in',
                'date_rel',
                'notes',
                'date_disign_finish',
                'name_client',
                'product_name',
                'disenador',
                'nesteo_chk'
              ], // Campos a leer
            ],
            kwargs: {
              limit: 100,
            },
          },
          id: Math.floor(Math.random() * 1000),
        };

        try {
            const readResponse = await fetch("/web/dataset/call_kw", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(readBody),
                credentials: "include",
            });

            const readData = await readResponse.json();
//            console.log("📦 Datos obtenidos:", readData.result);


              // Asigna los datos al estado
            this.state.items = readData.result;
            this.state.items = this.state.items.map(row =>(
                {
                    ...row,
                    diferencia: ((((new Date(row.date_disign_finish) - new Date().getTime()) / (1000 * 60 * 60 * 24)) + 1).toFixed(0)),
                    nesteo_chk: row.nesteo_chk?'✓':'',
//                    diferencia: row.date_in
                }
            ));
//            console.log("📦 Datos modificados:", this.state.items);




        } catch (error) {
          console.error("❌ Error al leer datos:", error);
        }
    });




  }
}

// 📌 **Asegúrate de que el nombre de la plantilla coincide exactamente**
Seguimiento.template = "dtm_odt.seguimiento";

// 📌 **Prueba cambiar la categoría del registro**
registry.category("actions").add("dtm_odt.seguimiento", Seguimiento);

//console.log("MiComponente registrado en web.client_actions");



