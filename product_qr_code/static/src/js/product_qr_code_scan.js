/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component , useRef, onMounted } from "@odoo/owl";

export class ProductQrcodeScanner extends Component{
    setup() {
        super.setup();
        this.result = useRef("result");
        this.reader = useRef("reader");
        this.orm = useService("orm");
        this.model = "product.qr.code";
        onMounted(() => {
             this.loadQrCodeScanner();
          });
    }

      loadQrCodeScanner() {
         var self=this
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
                if (value){
                    const trimmedValue = value.trim();
                    scannedData[trimmedKey] = trimmedValue;
                }
            }
             if (scannedData.hasOwnProperty('Product')) {
                scanner.clear();
                self.reader.el.classList.add('d-none');
                 const domain = [['id','=',parseInt(scannedData['Record_id']) ]];

                const qrCode = await self.orm.call(self.model, 'search_read', [domain]);
                if (qrCode.length === 0) {
                     var successMessage = document.createElement('h2');
                    successMessage.innerHTML = `<h2 style="color:red;">Invalid!</h2>`;
                    self.result.el.appendChild(successMessage);
                     var newelement = document.createElement('p');
                    newelement.innerHTML = `<p style="color:red;">No QR code Found For Product!!</p>`;
                    self.result.el.appendChild(newelement);

                } else {
                    var successMessage = document.createElement('h2');
                    successMessage.innerHTML = `<h2>Success!</h2>`;
                    self.result.el.appendChild(successMessage);
                    var newelement = document.createElement('p');

                    if(qrCode[0]['scanned']){
                        newelement.innerHTML = `<p style="color:green;">QR code Already Scanned.</p>`;
                    } else {
                          newelement.innerHTML = `<p style="color:green;">QR code Scanned Successfully.</p>`;
                        self.orm.call(self.model, 'mark_as_scanned', [qrCode[0]['id']]).then(function(){
                             location.reload();
                            });
                    }
                     self.result.el.appendChild(newelement);

                }
            } else {
                var invalidMessage = document.createElement('h2');
                invalidMessage.innerHTML = `<h2 style="color:red;">Invalid!</h2>`;
                self.result.el.appendChild(invalidMessage);
                scanner.clear();
                self.reader.el.classList.add('d-none');
            }

        }

         function error(err) {
            console.warn(err);// Prints any errors to the console
        }
    }

};

ProductQrcodeScanner.template = "product_qr_code.ProductQrcodeScanner";
registry.category("actions").add("scan_product_qrcode_client_action", ProductQrcodeScanner);