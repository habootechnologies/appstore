/** @odoo-module **/

// Odoo 15 / OWL 1: onMounted and useRef are OWL 2 APIs not available here.
// useService is an Odoo-layer hook available from Odoo 15 onward.
// UNVERIFIED: confirm useService("orm") resolves correctly on your Odoo 15 instance.
// DOM refs are accessed via this.refs.name (OWL 1 class-based ref API, no .el wrapper).

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class ProductQrcodeScanner extends Component {
    setup() {
        this.orm = useService("orm");
        this.model = "product.qr.code";
    }

    // OWL 1 lifecycle: mounted() replaces onMounted(() => {...}) hook
    async mounted() {
        this.loadQrCodeScanner();
    }

    loadQrCodeScanner() {
        var self = this;
        const scanner = new Html5QrcodeScanner('reader', {
            qrbox: {
                width: 250,
                height: 250,
            },
            fps: 20,
        });
        scanner.render(success, error);

        async function success(data) {
            const keyValuePairs = data.split(',');
            const scannedData = {};
            for (const pair of keyValuePairs) {
                const [key, value] = pair.split(':');
                const trimmedKey = key.trim();
                if (value) {
                    const trimmedValue = value.trim();
                    scannedData[trimmedKey] = trimmedValue;
                }
            }
            if (scannedData.hasOwnProperty('Product')) {
                scanner.clear();
                // OWL 1: refs accessed as this.refs.name (DOM element directly, no .el)
                self.refs.reader.classList.add('d-none');
                const domain = [['id', '=', parseInt(scannedData['Record_id'])]];

                const qrCode = await self.orm.call(self.model, 'search_read', [domain]);
                if (qrCode.length === 0) {
                    var successMessage = document.createElement('h2');
                    successMessage.innerHTML = `<h2 style="color:red;">Invalid!</h2>`;
                    self.refs.result.appendChild(successMessage);
                    var newelement = document.createElement('p');
                    newelement.innerHTML = `<p style="color:red;">No QR code Found For Product!!</p>`;
                    self.refs.result.appendChild(newelement);
                } else {
                    var successMessage = document.createElement('h2');
                    successMessage.innerHTML = `<h2>Success!</h2>`;
                    self.refs.result.appendChild(successMessage);
                    var newelement = document.createElement('p');

                    if (qrCode[0]['scanned']) {
                        newelement.innerHTML = `<p style="color:green;">QR code Already Scanned.</p>`;
                    } else {
                        newelement.innerHTML = `<p style="color:green;">QR code Scanned Successfully.</p>`;
                        self.orm.call(self.model, 'mark_as_scanned', [qrCode[0]['id']]).then(function () {
                            location.reload();
                        });
                    }
                    self.refs.result.appendChild(newelement);
                }
            } else {
                var invalidMessage = document.createElement('h2');
                invalidMessage.innerHTML = `<h2 style="color:red;">Invalid!</h2>`;
                self.refs.result.appendChild(invalidMessage);
                scanner.clear();
                self.refs.reader.classList.add('d-none');
            }
        }

        function error(err) {
            console.warn(err);
        }
    }
}

ProductQrcodeScanner.template = "haboo_qr_code.ProductQrcodeScanner";
registry.category("actions").add("scan_product_qrcode_client_action", ProductQrcodeScanner);
