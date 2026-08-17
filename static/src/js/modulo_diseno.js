/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ModuloDiseno extends Component {
    setup() {
        this.state = useState({
            ordenes: [],
            clients: [],
            ordenes_filtro: [],
            productos: [],
            asc: "",
            styleBarraTiempo: "",
            styleBarraFueraTiempo: "",
            kpiTotal: 0,
            kpiOdTiempo: 0,
            kpiOdFueraTiempo: 0,
            kpiClientes: 0,
            kpiDisenadores: 0,
            showPDF: false,
            currentPDF: null,
            pdfTitle: "",
        });

        onWillStart(async () => {
            this.loadOrdenes();
        });
    }

    openPDF(po_file) {
        this.state.currentPDF = po_file;
        this.state.showPDF = true;
    }

    closePDF() {
        this.state.showPDF = false;
    }

    async loadOrdenes() {
        const response = await fetch("/dtm_diseno");
        const data = await response.json();
        data.sort((a, b) => {
            const parseDate = (str) => {
                if (!str || str === "--/--/--") return null;
                // Suponiendo formato "dd/mm/yyyy"
                const [d, m, y] = str.split("/");
                return new Date(`${y}-${m}-${d}`);
            };

            const dateA = parseDate(a.fecha_termino_diseno);
            const dateB = parseDate(b.fecha_termino_diseno);

            if (!dateA && !dateB) return 0;   // ambos sin fecha
            if (!dateA) return 1;             // A sin fecha → va después
            if (!dateB) return -1;            // B sin fecha → va después

            return dateA - dateB;             // comparación normal
        });
        this.state.ordenes = data;
        this.state.ordenes_filtro = data;
        this.state.kpiTotal = data.length;
        const hoy = new Date();
        this.state.kpiOdTiempo = data.filter(item => new Date(item.fecha_termino_diseno) >= hoy).length;
        this.state.kpiOdFueraTiempo = data.filter(item => new Date(item.fecha_termino_diseno) < hoy).length;
        const clientes = data.map(x => x.cliente);
        this.state.clients = [...new Set(clientes)];
        this.state.kpiClientes = new Set(clientes).size;
        const productos = data.map(x => x.producto);
        this.state.productos = [...new Set(productos)];
        const entiempo = this.state.kpiTotal - this.state.kpiOdFueraTiempo;
        this.state.styleBarraTiempo = entiempo > 0 ? "background:var(--dc-accent2); width:'+ (entiempo)/this.state.kpiTotal*100+'%'" : "background:var(--dc-accent2); width:0%";
        const fueraTiempo = this.state.kpiTotal - this.state.kpiOdTiempo;
        this.state.styleBarraFueraTiempo = fueraTiempo > 0 ? "background:var(--dc-amber); width:'+ (fueraTiempo)/this.state.kpiTotal*100+'%'" : "background:var(--dc-amber); width:0%";
    }

    // Filtros
    clienteFiltro(ev) {
        const cliente = ev.target.value;
        this.state.ordenes = cliente === "" ? this.state.ordenes_filtro : this.state.ordenes_filtro.filter(item => item.cliente === cliente);
        const productos = this.state.ordenes.map(x => x.producto);
        this.state.productos = [...new Set(productos)];
    }

    productoFiltro(ev) {
        const producto = ev.target.value;
        this.state.ordenes = producto === "" ? this.state.ordenes_filtro : this.state.ordenes_filtro.filter(item => item.producto === producto);
        const clientes = this.state.ordenes.map(x => x.cliente);
        this.state.clients = [...new Set(clientes)];
    }

    sortColumn(column) {
        if (this.state.asc !== column) {
            this.state.ordenes.sort((a, b) => {
                if (a[column] < b[column]) return -1;
                if (a[column] > b[column]) return 1;
                return 0;
            });
            this.state.asc = column;
        } else {
            this.state.ordenes.sort((a, b) => {
                if (a[column] > b[column]) return -1;
                if (a[column] < b[column]) return 1;
                return 0;
            });
            this.state.asc = "";
        }

    }

    searchODT(ev) {
        const search = ev.target.value;
        console.log(search);
        this.state.ordenes = search === "" ? this.state.ordenes_filtro : this.state.ordenes_filtro.filter(item => item.orden_diseno === parseInt(search));
        console.log("this.state.ordenes", this.state.ordenes);
    }

}

ModuloDiseno.template = "dtm_odt.modulo_diseno";
registry.category("actions").add("dtm_odt.modulo_diseno", ModuloDiseno);