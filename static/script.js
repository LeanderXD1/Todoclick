document.addEventListener('DOMContentLoaded', function() {
    // Activar animación de entrada de la página
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('loaded');
    }

    // Lógica del Carrito
    const cartIcon = document.querySelector('.cart-icon'); // Usamos la clase
    const cartModal = document.getElementById('cart-modal');
    const closeButton = document.querySelector('.close-button');
    const productList = document.getElementById('product-list'); // En productos.html
    const whatsappBtnFinal = document.getElementById('whatsapp-btn-after-payment'); // Este es tu nuevo botón principal del carrito
    
    // Tu número de WhatsApp REAL
    const phoneNumber = "584241216947";

    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // Función para actualizar la visualización del carrito
    function updateCartDisplay() {
        const cartItemsDiv = document.getElementById('cart-items');
        const cartCountSpan = document.getElementById('cart-count');
        const cartTotalPriceSpan = document.getElementById('cart-total-price');

        cartItemsDiv.innerHTML = '';
        let total = 0;

        if (cart.length === 0) {
            cartItemsDiv.innerHTML = '<p>El carrito está vacío.</p>';
            // Oculta el botón de WhatsApp si el carrito está vacío
            if (whatsappBtnFinal) whatsappBtnFinal.style.display = 'none';
        } else {
            // Muestra el botón de WhatsApp si hay ítems
            if (whatsappBtnFinal) whatsappBtnFinal.style.display = 'block';
            cart.forEach((item, index) => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'cart-item';
                itemDiv.innerHTML = `
                    <span>${item.name} (x${item.quantity})</span>
                    <span>$${(item.price * item.quantity).toFixed(2)}</span>
                    <button class="remove-from-cart" data-index="${index}">Eliminar</button>
                `;
                cartItemsDiv.appendChild(itemDiv);
                total += item.price * item.quantity;
            });
        }

        cartCountSpan.textContent = cart.length;
        cartTotalPriceSpan.textContent = `$${total.toFixed(2)}`;
    }

    // Añadir al Carrito (desde la página de productos)
    if (productList) { // Solo si estamos en la página de productos
        productList.addEventListener('click', function(event) {
            if (event.target.classList.contains('add-to-cart')) {
                const name = event.target.dataset.name;
                const price = parseFloat(event.target.dataset.price);

                const existingItem = cart.find(item => item.name === name);

                if (existingItem) {
                    existingItem.quantity++;
                } else {
                    cart.push({ name, price, quantity: 1 });
                }

                localStorage.setItem('cart', JSON.stringify(cart));
                updateCartDisplay();
                alert(`${name} añadido al carrito.`);
            }
        });
    }

    // Eliminar del Carrito (dentro del modal)
    if (cartModal) { // Solo si el modal existe en la página
        cartModal.addEventListener('click', function(event) {
            if (event.target.classList.contains('remove-from-cart')) {
                const index = parseInt(event.target.dataset.index);
                cart.splice(index, 1); // Elimina el elemento por su índice
                localStorage.setItem('cart', JSON.stringify(cart));
                updateCartDisplay();
            }
        });
    }

    // Abrir/Cerrar Modal del Carrito
    if (cartIcon) {
        cartIcon.addEventListener('click', function() {
            cartModal.style.display = 'block';
            updateCartDisplay(); // Asegura que el carrito esté actualizado al abrir
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', function() {
            cartModal.style.display = 'none';
        });
    }

    window.addEventListener('click', function(event) {
        if (event.target === cartModal) {
            cartModal.style.display = 'none';
        }
    });

    // Evento para el botón "Confirmar Pedido por WhatsApp"
    if (whatsappBtnFinal) {
        whatsappBtnFinal.addEventListener('click', function() {
            if (cart.length === 0) {
                alert("Tu carrito está vacío. Agrega productos antes de finalizar el pedido.");
                return;
            }

            let orderSummary = "¡Hola! Quisiera confirmar mi pedido de Dulces Deliciosos (pago en efectivo al recibir):\n\n";
            cart.forEach(item => {
                orderSummary += `- ${item.name} (x${item.quantity}) - $${(item.price * item.quantity).toFixed(2)}\n`;
            });

            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            orderSummary += `\nTotal a pagar en efectivo: $${total.toFixed(2)}\n\n`;
            orderSummary += "Por favor, indícame la disponibilidad y cómo coordinamos la entrega. ¡Gracias!";

            const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(orderSummary)}`;
            
            window.open(whatsappUrl, '_blank');

            // Opcional: Limpiar el carrito después de enviar el pedido
            cart = [];
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartDisplay();
            // Cierra el modal después de enviar el pedido
            cartModal.style.display = 'none';
        });
    }

    // Llama a updateCartDisplay al cargar la página para inicializar el carrito y el contador
    updateCartDisplay();
});