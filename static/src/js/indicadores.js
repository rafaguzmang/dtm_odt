/** @odoo-module **/


import { Component, useState, useRef, onMounted   } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class Indicadores extends Component{
    setup(){
            super.setup();
            this.canvasRef = useRef("grafico");
            this.state = useState({
                indicadores:[]
            });

            onMounted(async()=>{
                await new Promise(resolve => setTimeout(resolve, 100));

                // Chart desde CDN
                const Chart = window.Chart;

                // Registra plugin si está cargado
                if (window['chartjs-plugin-annotation']) {
                    Chart.register(window['chartjs-plugin-annotation']);
                }


                try {
                    const response = await fetch('/diseno_indicadores',{
                    method:'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body:JSON.stringify({})
                    })

                    const data = await response.json();
                    this.state.indicadores = data.result;
                    console.log(this.state.indicadores);

                    const canvas = this.canvasRef.el;
                    const ctx = canvas.getContext("2d");

                    const labels = this.state.indicadores.map(item => item.mes);
                    const datos = this.state.indicadores.map(item => item.porciento);
                    console.log(labels);
                    console.log(datos);
//                    Grafica
                    new Chart(ctx, {
                        type: "bar", // o "line", "pie", etc.
                        data: {
                          labels: labels,
                          datasets: [{
                              label: "Calidad",
                              data: datos,
                              backgroundColor: "rgba(75, 192, 192, 0.2)",
                              borderColor: "rgba(75, 192, 192, 1)",
                              borderWidth: 1
                          }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                annotation: {
                                    annotations: {
                                        line1: {
                                            type: 'line',
                                            yMin: 85,
                                            yMax: 85,
                                            borderColor: 'rgba(0, 255, 0, 0.4)',
                                            borderWidth: 1,
                                            label: {
                                                content: '',
                                                enabled: true,
                                                position: 'start'
                                            }
                                        }
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100  // Escala de 0 a 100
                                }
                            }
                        }
                    });



                }catch (error) {
                  console.error("❌ Error al leer datos:", error);
                }

            });
           onMounted(()=>{



           });
       }
}

Indicadores.template = "dtm_odt.indicadores";
registry.category("actions").add("dtm_odt.indicadores",Indicadores);