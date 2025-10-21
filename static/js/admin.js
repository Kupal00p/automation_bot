// QuickSell Admin Dashboard
let salesChart, statusChart;
let allOrders = [];

document.addEventListener('DOMContentLoaded', () => {
    updateTime();
    setInterval(updateTime, 1000);
    loadDashboard();
});

function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString('en-US', { 
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
}

function showSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    document.querySelectorAll('.nav-link').forEach(l => {
        l.classList.remove('bg-indigo-700');
        l.classList.add('hover:bg-indigo-700');
    });
    
    document.getElementById(`section-${section}`).classList.remove('hidden');
    event.target.closest('.nav-link').classList.add('bg-indigo-700');
    
    if (section === 'orders') loadOrders();
    else if (section === 'analytics') loadAnalytics();
    else if (section === 'verifications') loadVerifications();
}

async function loadDashboard() {
    try {
        const stats = await fetch('/admin/api/stats').then(r => r.json());
        const orders = await fetch('/admin/api/orders?limit=10').then(r => r.json());
        
        updateStats(stats);
        displayRecentOrders(orders.orders);
        updateCharts(stats);
        
        // Load verification count
        loadVerifications();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        alert('⚠️ Error loading dashboard. Please refresh the page.');
    }
}

function updateStats(stats) {
    document.getElementById('stat-total-orders').textContent = stats.total_orders || 0;
    document.getElementById('stat-revenue').textContent = formatCurrency(stats.total_revenue || 0);
    document.getElementById('stat-pending-orders').textContent = stats.pending_orders || 0;
    document.getElementById('stat-active-users').textContent = stats.active_users || 0;
    document.getElementById('pending-count').textContent = stats.pending_orders || 0;
}

function updateCharts(stats) {
    // Sales chart with real data
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    if (salesChart) salesChart.destroy();
    
    const weeklySales = stats.weekly_sales || [0, 0, 0, 0, 0, 0, 0];
    
    salesChart = new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Sales (₱)',
                data: weeklySales,
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₱' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    // Status chart with real data
    const statusCtx = document.getElementById('statusChart').getContext('2d');
    if (statusChart) statusChart.destroy();
    
    const statusCounts = stats.order_status_counts || [0, 0, 0, 0, 0];
    
    statusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered'],
            datasets: [{
                data: statusCounts,
                backgroundColor: ['#fbbf24', '#3b82f6', '#8b5cf6', '#10b981', '#22c55e']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function displayRecentOrders(orders) {
    const html = orders.map(o => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4">${o.order_number}</td>
            <td class="px-6 py-4">${o.customer_name || 'N/A'}</td>
            <td class="px-6 py-4">₱${formatCurrency(o.total_amount)}</td>
            <td class="px-6 py-4">${getStatusBadge(o.order_status)}</td>
            <td class="px-6 py-4">${formatDate(o.created_at)}</td>
            <td class="px-6 py-4">
                <button onclick="viewOrder(${o.id})" class="text-indigo-600">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    document.getElementById('recent-orders-list').innerHTML = `
        <table class="min-w-full"><tbody>${html}</tbody></table>
    `;
}

async function loadOrders() {
    try {
        // Show loading state
        document.getElementById('orders-table').innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-spinner fa-spin text-4xl text-indigo-600 mb-3"></i>
                <p class="text-gray-600">Loading orders...</p>
            </div>
        `;
        
        const data = await fetch('/admin/api/orders?limit=100').then(r => r.json());
        allOrders = data.orders || [];
        displayOrdersTable(allOrders);
    } catch (error) {
        console.error('Error loading orders:', error);
        document.getElementById('orders-table').innerHTML = `
            <div class="text-center py-12 text-red-500">
                <i class="fas fa-exclamation-triangle text-5xl mb-4"></i>
                <p class="text-lg">Error loading orders</p>
                <button onclick="loadOrders()" class="mt-4 bg-indigo-600 text-white px-4 py-2 rounded-lg">Retry</button>
            </div>
        `;
    }
}

function displayOrdersTable(orders) {
    if (!orders || orders.length === 0) {
        document.getElementById('orders-table').innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <i class="fas fa-inbox text-5xl mb-4 text-gray-300"></i>
                <p class="text-lg">No orders found</p>
            </div>
        `;
        return;
    }
    
    const html = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order #</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${orders.map(o => `
                    <tr class="hover:bg-gray-50 transition">
                        <td class="px-6 py-4 whitespace-nowrap font-medium text-indigo-600">${o.order_number}</td>
                        <td class="px-6 py-4 whitespace-nowrap">${o.customer_name || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">${o.items?.length || 0}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right font-semibold">₱${formatCurrency(o.total_amount)}</td>
                        <td class="px-6 py-4 whitespace-nowrap uppercase text-sm">${o.payment_method}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">${getStatusBadge(o.order_status)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${formatDate(o.created_at)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            <button onclick="viewOrder(${o.id})" class="text-indigo-600 hover:text-indigo-900 mr-3" title="View Details">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${o.order_status === 'pending' ? `
                            <button onclick="confirmOrder(${o.id})" class="text-green-600 hover:text-green-900" title="Confirm Order">
                                <i class="fas fa-check"></i>
                            </button>
                            ` : ''}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    document.getElementById('orders-table').innerHTML = html;
}

async function viewOrder(id) {
    try {
        // Show loading in modal
        document.getElementById('orderModalContent').innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-spinner fa-spin text-5xl text-indigo-600 mb-4"></i>
                <p class="text-gray-600">Loading order details...</p>
            </div>
        `;
        document.getElementById('orderModal').classList.remove('hidden');
        document.getElementById('orderModal').classList.add('flex');
        
        const order = await fetch(`/admin/api/orders/${id}`).then(r => r.json());
        
        let html = `
            <div class="space-y-6">
                <!-- Order Header -->
                <div class="border-b pb-4">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="text-2xl font-bold text-indigo-600">${order.order_number || 'N/A'}</h3>
                            <p class="text-gray-600 mt-1">${order.created_at ? formatDate(order.created_at) : 'N/A'}</p>
                        </div>
                        <div class="text-right">
                            ${order.order_status ? getStatusBadge(order.order_status) : '<span class="text-gray-500">No Status</span>'}
                            <p class="text-sm text-gray-600 mt-1">${order.payment_method ? order.payment_method.toUpperCase() : 'N/A'}</p>
                        </div>
                    </div>
                </div>

                <!-- Customer Information -->
                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <i class="fas fa-user mr-2 text-indigo-600"></i>
                        Customer Information
                    </h4>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <p class="text-sm text-gray-600">Name</p>
                            <p class="font-medium">${order.delivery_info?.recipient_name || order.facebook_name || 'N/A'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Phone</p>
                            <p class="font-medium">${order.delivery_info?.phone || order.phone || 'N/A'}</p>
                        </div>
                        <div class="col-span-2">
                            <p class="text-sm text-gray-600">Delivery Address</p>
                            <p class="font-medium">${order.delivery_info?.address || 'N/A'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Customer Tier</p>
                            <p class="font-medium capitalize">${order.customer_tier || 'Regular'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Total Orders</p>
                            <p class="font-medium">${order.user_total_orders || 0} orders</p>
                        </div>
                    </div>
                </div>

                <!-- Verification Section -->
                ${order.verification_required ? `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <i class="fas fa-shield-check mr-2 text-yellow-600"></i>
                        Verification Required
                    </h4>
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <p class="text-sm text-gray-600">Verification Status</p>
                            <p class="font-medium capitalize ${
                                order.verification_status === 'verified' ? 'text-green-600' :
                                order.verification_status === 'rejected' ? 'text-red-600' :
                                order.verification_status === 'under_review' ? 'text-blue-600' :
                                'text-yellow-600'
                            }">${order.verification_status || 'Pending'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Verification Type</p>
                            <p class="font-medium capitalize">${order.verification_type || 'Not selected'}</p>
                        </div>
                    </div>
                    
                    ${order.verification ? `
                        ${order.verification.verification_type === 'id_verification' ? `
                            <!-- ID Verification Images -->
                            <div class="space-y-3">
                                <p class="font-semibold text-sm text-gray-700">Submitted Documents:</p>
                                <div class="grid grid-cols-2 gap-4">
                                    ${order.verification.id_image_url ? `
                                        <div>
                                            <p class="text-xs text-gray-600 mb-2">Valid ID</p>
                                            <a href="${order.verification.id_image_url}" target="_blank" class="block">
                                                <img src="${order.verification.id_image_url}" 
                                                     class="w-full h-48 object-cover rounded-lg border-2 border-gray-300 hover:border-indigo-500 cursor-pointer transition"
                                                     data-image-url="${order.verification.id_image_url}"
                                                     alt="Valid ID">
                                            </a>
                                            <p class="text-xs text-gray-500 mt-1">${order.verification.id_type || 'Unknown ID'}</p>
                                        </div>
                                    ` : ''}
                                    ${order.verification.selfie_image_url ? `
                                        <div>
                                            <p class="text-xs text-gray-600 mb-2">Selfie with ID</p>
                                            <a href="${order.verification.selfie_image_url}" target="_blank" class="block">
                                                <img src="${order.verification.selfie_image_url}" 
                                                     class="w-full h-48 object-cover rounded-lg border-2 border-gray-300 hover:border-indigo-500 cursor-pointer transition"
                                                     data-image-url="${order.verification.selfie_image_url}"
                                                     alt="Selfie with ID">
                                            </a>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        ` : order.verification.verification_type === 'upfront_payment' ? `
                            <!-- Payment Proof -->
                            <div class="space-y-3">
                                <p class="font-semibold text-sm text-gray-700">Payment Proof:</p>
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <p class="text-sm text-gray-600">Upfront Amount</p>
                                        <p class="font-medium text-lg">₱${formatCurrency(order.verification.upfront_amount)}</p>
                                        <p class="text-xs text-gray-500">${order.verification.payment_method}</p>
                                    </div>
                                    ${order.verification.payment_proof_url ? `
                                        <div>
                                            <p class="text-xs text-gray-600 mb-2">Payment Screenshot</p>
                                            <a href="${order.verification.payment_proof_url}" target="_blank" class="block">
                                                <img src="${order.verification.payment_proof_url}" 
                                                     class="w-full h-48 object-cover rounded-lg border-2 border-gray-300 hover:border-indigo-500 cursor-pointer transition"
                                                     data-image-url="${order.verification.payment_proof_url}"
                                                     alt="Payment Proof">
                                            </a>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${order.verification.rejection_reason ? `
                            <div class="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                                <p class="text-sm font-semibold text-red-800">Rejection Reason:</p>
                                <p class="text-sm text-red-700">${order.verification.rejection_reason}</p>
                            </div>
                        ` : ''}
                        
                        ${order.verification.verification_status === 'under_review' || order.verification.verification_status === 'pending' ? `
                            <div class="mt-4 flex gap-3">
                                <button onclick="approveVerification(${order.id})" class="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition">
                                    <i class="fas fa-check mr-2"></i>Approve Verification
                                </button>
                                <button onclick="rejectVerification(${order.id})" class="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition">
                                    <i class="fas fa-times mr-2"></i>Reject Verification
                                </button>
                            </div>
                        ` : ''}
                    ` : '<p class="text-sm text-gray-600">Waiting for customer to submit verification...</p>'}
                </div>
                ` : ''}

                <!-- Order Items -->
                <div>
                    <h4 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <i class="fas fa-shopping-bag mr-2 text-indigo-600"></i>
                        Order Items
                    </h4>
                    <div class="border rounded-lg overflow-hidden">
                        <table class="w-full">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">Product</th>
                                    <th class="px-4 py-3 text-center text-sm font-medium text-gray-700">Qty</th>
                                    <th class="px-4 py-3 text-right text-sm font-medium text-gray-700">Price</th>
                                    <th class="px-4 py-3 text-right text-sm font-medium text-gray-700">Total</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200">
                                ${(order.items || []).map(item => `
                                    <tr>
                                        <td class="px-4 py-3">
                                            <p class="font-medium text-gray-900">${item.product_name}</p>
                                            <p class="text-xs text-gray-500">${item.sku || ''}</p>
                                        </td>
                                        <td class="px-4 py-3 text-center">${item.quantity}</td>
                                        <td class="px-4 py-3 text-right">₱${formatCurrency(item.unit_price)}</td>
                                        <td class="px-4 py-3 text-right font-semibold">₱${formatCurrency(item.total_price)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Order Summary -->
                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-800 mb-3">Order Summary</h4>
                    <div class="space-y-2">
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600">Subtotal</span>
                            <span class="font-medium">₱${formatCurrency(order.subtotal || 0)}</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600">Shipping Fee</span>
                            <span class="font-medium">₱${formatCurrency(order.shipping_fee || 0)}</span>
                        </div>
                        ${parseFloat(order.discount_amount || 0) > 0 ? `
                        <div class="flex justify-between text-sm text-green-600">
                            <span>Discount</span>
                            <span class="font-medium">-₱${formatCurrency(order.discount_amount)}</span>
                        </div>
                        ` : ''}
                        ${parseFloat(order.upfront_paid || 0) > 0 ? `
                        <div class="flex justify-between text-sm text-blue-600">
                            <span>Upfront Paid</span>
                            <span class="font-medium">₱${formatCurrency(order.upfront_paid)}</span>
                        </div>
                        ` : ''}
                        <div class="border-t pt-2 flex justify-between">
                            <span class="font-semibold text-gray-900">Total Amount</span>
                            <span class="font-bold text-xl text-indigo-600">₱${formatCurrency(order.total_amount || 0)}</span>
                        </div>
                        ${parseFloat(order.remaining_balance || 0) > 0 && parseFloat(order.remaining_balance || 0) !== parseFloat(order.total_amount || 0) ? `
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600">Remaining Balance (COD)</span>
                            <span class="font-semibold text-orange-600">₱${formatCurrency(order.remaining_balance)}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Actions -->
                ${order.order_status === 'pending' && !order.verification_required || order.verification_status === 'verified' ? `
                <div class="flex gap-3 pt-4 border-t">
                    <button onclick="confirmOrder(${order.id}, true)" class="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg transition font-semibold">
                        <i class="fas fa-check mr-2"></i>Confirm Order
                    </button>
                    <button onclick="cancelOrder(${order.id}, true)" class="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-3 rounded-lg transition font-semibold">
                        <i class="fas fa-times mr-2"></i>Cancel Order
                    </button>
                </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('orderModalContent').innerHTML = html;
        
        // Add click handlers for verification images
        setTimeout(() => {
            const images = document.querySelectorAll('[data-image-url]');
            images.forEach(img => {
                img.addEventListener('click', function(e) {
                    e.preventDefault();
                    openImageModal(this.getAttribute('data-image-url'));
                });
            });
        }, 100);
        
    } catch (error) {
        console.error('Error loading order:', error);
        document.getElementById('orderModalContent').innerHTML = `
            <div class="text-center py-12 text-red-500">
                <i class="fas fa-exclamation-triangle text-5xl mb-4"></i>
                <p class="text-lg">Error loading order details</p>
                <p class="text-sm mt-2">${error.message}</p>
                <button onclick="closeOrderModal()" class="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg">Close</button>
            </div>
        `;
    }
}

function closeOrderModal() {
    const modal = document.getElementById('orderModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function confirmOrder(id, fromModal = false) {
    if (!confirm('Confirm this order? Customer will be notified.')) return;
    
    try {
        const response = await fetch(`/admin/api/orders/${id}/confirm`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Order confirmed successfully!');
            if (fromModal) {
                closeOrderModal();
            }
            refreshData();
            loadOrders();
        } else {
            alert('❌ Error: ' + (data.error || 'Failed to confirm order'));
        }
    } catch (error) {
        console.error('Error confirming order:', error);
        alert('Network error occurred');
    }
}

async function cancelOrder(id, fromModal = false) {
    const reason = prompt('Enter cancellation reason:');
    if (!reason || reason.trim() === '') return;
    
    try {
        const response = await fetch(`/admin/api/orders/${id}/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason.trim() })
        });
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Order cancelled successfully!');
            if (fromModal) {
                closeOrderModal();
            }
            refreshData();
            loadOrders();
        } else {
            alert('❌ Error: ' + (data.error || 'Failed to cancel order'));
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        alert('Network error occurred');
    }
}

function refreshData() {
    loadDashboard();
}

async function logout() {
    await fetch('/admin/logout', { method: 'POST' });
    window.location.href = '/admin/login';
}

function formatCurrency(v) {
    return parseFloat(v).toFixed(2);
}

function formatDate(d) {
    return new Date(d).toLocaleString();
}

function getStatusBadge(s) {
    const styles = {
        pending: 'bg-yellow-100 text-yellow-800',
        confirmed: 'bg-blue-100 text-blue-800',
        processing: 'bg-purple-100 text-purple-800',
        shipped: 'bg-indigo-100 text-indigo-800',
        delivered: 'bg-green-100 text-green-800',
        cancelled: 'bg-red-100 text-red-800'
    };
    const style = styles[s] || 'bg-gray-100 text-gray-800';
    return `<span class="px-3 py-1 text-xs font-semibold rounded-full ${style} capitalize">${s}</span>`;
}

async function loadAnalytics() {
    try {
        const stats = await fetch('/admin/api/stats').then(r => r.json());
        
        // Update customer insights
        document.getElementById('new-customers').textContent = stats.new_customers || 0;
        document.getElementById('repeat-customers').textContent = stats.repeat_customers || 0;
        document.getElementById('avg-order-value').textContent = formatCurrency(stats.avg_order_value || 0);
        
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart')?.getContext('2d');
        if (revenueCtx) {
            const monthlyRevenue = stats.monthly_revenue || [];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
            
            new Chart(revenueCtx, {
                type: 'bar',
                data: {
                    labels: months.slice(0, monthlyRevenue.length),
                    datasets: [{
                        label: 'Revenue (₱)',
                        data: monthlyRevenue,
                        backgroundColor: 'rgba(99, 102, 241, 0.8)',
                        borderColor: 'rgb(99, 102, 241)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₱' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Top Products Chart
        const productsCtx = document.getElementById('productsChart')?.getContext('2d');
        if (productsCtx && stats.top_products) {
            const products = stats.top_products.slice(0, 5);
            
            new Chart(productsCtx, {
                type: 'horizontalBar',
                data: {
                    labels: products.map(p => p.name),
                    datasets: [{
                        label: 'Units Sold',
                        data: products.map(p => p.total_sold),
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

async function loadVerifications() {
    try {
        const data = await fetch('/admin/api/verifications/pending').then(r => r.json());
        document.getElementById('verification-count').textContent = data.count || 0;
        
        const verifications = data.verifications || [];
        
        if (verifications.length === 0) {
            document.getElementById('verifications-list').innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i class="fas fa-check-circle text-5xl mb-4 text-green-300"></i>
                    <p class="text-lg">No pending verifications</p>
                    <p class="text-sm mt-2">All verifications have been processed</p>
                </div>
            `;
            return;
        }
        
        const html = verifications.map(v => `
            <div class="border-b border-gray-200 py-4 hover:bg-gray-50 transition">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center gap-3">
                            <span class="font-semibold text-indigo-600">${v.order_number}</span>
                            <span class="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">${v.verification_type}</span>
                        </div>
                        <p class="text-sm text-gray-600 mt-1">
                            <i class="fas fa-user mr-1"></i>${v.facebook_name || 'Unknown'} • 
                            <i class="fas fa-phone mr-1"></i>${v.phone || 'N/A'}
                        </p>
                        <p class="text-sm text-gray-500 mt-1">
                            Amount: <span class="font-semibold">₱${formatCurrency(v.total_amount)}</span> • 
                            Submitted: ${formatDate(v.submitted_at)}
                        </p>
                    </div>
                    <button onclick="viewOrder(${v.order_id})" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm transition">
                        <i class="fas fa-eye mr-2"></i>Review
                    </button>
                </div>
            </div>
        `).join('');
        
        document.getElementById('verifications-list').innerHTML = html;
    } catch (error) {
        console.error('Error loading verifications:', error);
        document.getElementById('verifications-list').innerHTML = `
            <div class="text-center py-12 text-red-500">
                <i class="fas fa-exclamation-triangle text-5xl mb-4"></i>
                <p class="text-lg">Error loading verifications</p>
            </div>
        `;
    }
}

function filterOrders() {
    const status = document.getElementById('filter-status').value;
    const filtered = status ? allOrders.filter(o => o.order_status === status) : allOrders;
    displayOrdersTable(filtered);
}

function searchOrders() {
    const searchTerm = document.getElementById('search-order').value.toLowerCase().trim();
    const status = document.getElementById('filter-status').value;
    
    let filtered = allOrders;
    
    // Filter by status first
    if (status) {
        filtered = filtered.filter(o => o.order_status === status);
    }
    
    // Then filter by search term
    if (searchTerm) {
        filtered = filtered.filter(o => 
            o.order_number.toLowerCase().includes(searchTerm) ||
            (o.customer_name && o.customer_name.toLowerCase().includes(searchTerm))
        );
    }
    
    displayOrdersTable(filtered);
}

function exportOrders() {
    alert('Export feature coming soon');
}

// Verification functions
async function approveVerification(orderId) {
    if (!confirm('Approve this verification? This will confirm the order.')) return;
    
    try {
        const response = await fetch(`/admin/api/verifications/${orderId}/approve`, {
            method: 'POST'
        });
        
        if (response.ok) {
            alert('Verification approved! Order confirmed.');
            closeOrderModal();
            refreshData();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to approve'));
        }
    } catch (error) {
        console.error('Error approving verification:', error);
        alert('Network error occurred');
    }
}

async function rejectVerification(orderId) {
    const reason = prompt('Enter rejection reason (e.g., "ID not clear", "ID does not match"):');
    if (!reason || reason.trim() === '') return;
    
    try {
        const response = await fetch(`/admin/api/verifications/${orderId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason.trim() })
        });
        
        if (response.ok) {
            alert('Verification rejected. Customer will be notified to resubmit.');
            closeOrderModal();
            refreshData();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to reject'));
        }
    } catch (error) {
        console.error('Error rejecting verification:', error);
        alert('Network error occurred');
    }
}

function openImageModal(imageUrl) {
    // Create image modal
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4';
    modal.onclick = function() { document.body.removeChild(modal); };
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.className = 'max-w-full max-h-full object-contain';
    img.onclick = function(e) { e.stopPropagation(); };
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '<i class="fas fa-times"></i>';
    closeBtn.className = 'absolute top-4 right-4 text-white text-3xl hover:text-gray-300';
    closeBtn.onclick = function() { document.body.removeChild(modal); };
    
    modal.appendChild(img);
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);
}
