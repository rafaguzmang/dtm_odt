odoo.define('dtm_odt.script_backend', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderView: function () {
            return this._super.apply(this, arguments).then(() => {
                console.log("Checking rows to hide delete button...");

                // Busca el botón delete en función de la condición de `comprado`
                this.$el.find('tbody tr').each(function () {
                    const $row = $(this);
                    const comprado = $row.find('td[data-field="comprado"]').text().trim();
                    if (comprado === 'True') {
                        $row.find('button[name="delete"]').hide();
                    }
                });
            });
        },
    });
});



