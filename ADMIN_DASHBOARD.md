# QuickSell Admin Dashboard

## 🎯 Overview

A comprehensive admin dashboard for managing orders, tracking analytics, and monitoring verifications for the QuickSell e-commerce chatbot.

## ✨ Features

### 📊 Dashboard
- **Real-time Statistics**
  - Total orders and revenue
  - Pending orders count
  - Active users (last 30 days)
  - Revenue trends

- **Interactive Charts**
  - Weekly sales line chart
  - Order status distribution (doughnut chart)
  - Revenue trends
  - Top products

- **Recent Orders Table**
  - Quick view of last 10 orders
  - One-click order actions
  - Status indicators

### 📦 Orders Management
- **Order List** with advanced filtering
  - Filter by status (pending, confirmed, processing, shipped, delivered, cancelled)
  - Search by order number or customer name
  - Export to CSV (coming soon)

- **Order Details Modal**
  - Complete order information
  - Customer details
  - Itemized list with prices
  - Order totals breakdown
  - Quick actions (Confirm/Cancel)

- **Order Actions**
  - Confirm orders
  - Cancel orders with reason
  - Update order status
  - Automatic customer notifications

### 📈 Analytics
- **Revenue Analytics**
  - Monthly revenue chart (last 6 months)
  - Weekly sales trends
  - Average order value

- **Customer Insights**
  - New customers count
  - Repeat customers
  - Customer growth trends

- **Product Analytics**
  - Top 5 selling products
  - Sales volume by product
  - Low stock alerts

### ✅ Verifications
- **Pending Verifications List**
  - ID verification requests
  - Upfront payment verifications
  - Review verification documents
  - Approve/Reject with reasons

## 🚀 Getting Started

### 1. Access the Dashboard

Navigate to: `http://localhost:5000/admin/login`

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **Security Note**: Change these credentials immediately in production!

### 2. Dashboard Sections

#### Main Dashboard
- Overview of key metrics
- Visual charts for quick insights
- Recent orders at a glance

#### Orders
- Complete order management
- Filter and search capabilities
- Bulk actions (coming soon)

#### Analytics
- Deep dive into sales data
- Customer behavior analysis
- Product performance metrics

#### Verifications
- Review pending verifications
- Approve/reject with one click
- Track verification history

## 📱 Key Workflows

### Confirming an Order

1. Navigate to **Orders** section
2. Click the **eye icon** to view order details
3. Review order information
4. Click **Confirm Order**
5. Customer receives automatic notification

### Cancelling an Order

1. Find the order in Orders list
2. Click **Cancel** (X icon)
3. Enter cancellation reason
4. Stock is automatically restored
5. Customer receives cancellation notification

### Reviewing Verifications

1. Go to **Verifications** section
2. View pending verification requests
3. Review uploaded documents/proof
4. Click **Approve** or **Reject**
5. Customer receives status update

## 🎨 Dashboard Components

### Statistics Cards
```
┌─────────────────────────────┐
│ Total Orders         │ 245  │
│ ├─ Revenue      ₱125,000   │
│ ├─ Pending           12    │
│ └─ Active Users      89    │
└─────────────────────────────┘
```

### Charts
- **Line Chart**: Sales trends over time
- **Doughnut Chart**: Order status breakdown
- **Bar Chart**: Monthly revenue comparison
- **Horizontal Bar**: Top products

### Orders Table
| Order # | Customer | Items | Amount | Status | Actions |
|---------|----------|-------|--------|--------|---------|
| QS-001  | John Doe | 3     | ₱5,500 | Pending| 👁 ✓ ✗  |

## 🔐 Security Features

- Session-based authentication
- Login required for all admin routes
- Automatic logout on session expiry
- CSRF protection (recommended)

## 🛠️ Technical Details

### Tech Stack
- **Frontend**: HTML5, TailwindCSS, Chart.js
- **Backend**: Flask, Python
- **Database**: MySQL
- **API**: RESTful JSON API

### API Endpoints

#### Authentication
- `GET/POST /admin/login` - Login page and authentication
- `POST /admin/logout` - Logout

#### Dashboard
- `GET /admin/dashboard` - Main dashboard page
- `GET /admin/api/stats` - Dashboard statistics

#### Orders
- `GET /admin/api/orders` - List orders (with filters)
- `GET /admin/api/orders/<id>` - Get order details
- `POST /admin/api/orders/<id>/confirm` - Confirm order
- `POST /admin/api/orders/<id>/cancel` - Cancel order
- `PUT /admin/api/orders/<id>/status` - Update order status

#### Verifications
- `GET /admin/api/verifications/pending` - Get pending verifications
- `GET /admin/api/verifications/<id>` - Get verification details
- `POST /admin/api/verifications/<id>/approve` - Approve verification
- `POST /admin/api/verifications/<id>/reject` - Reject verification

#### Search
- `GET /admin/api/search?q=<query>` - Search orders by number

#### Activity
- `GET /admin/api/activity` - Get recent activity log

## 📊 Analytics Metrics Explained

### Total Orders
Count of all orders excluding cancelled ones.

### Total Revenue
Sum of all completed order amounts.

### Pending Orders
Orders waiting for admin confirmation.

### Active Users
Unique customers who placed orders in the last 30 days.

### Average Order Value
Mean value of all non-cancelled orders.

### Order Status Distribution
Breakdown of orders by their current status.

## 🎯 Best Practices

1. **Review pending orders daily**
   - Check for new orders at least twice per day
   - Confirm legitimate orders promptly

2. **Monitor verifications**
   - Review verification requests within 24 hours
   - Provide clear rejection reasons

3. **Track analytics weekly**
   - Review sales trends every Monday
   - Identify top-performing products
   - Monitor customer retention

4. **Handle cancellations properly**
   - Always provide specific reasons
   - Check if customer needs assistance

5. **Security**
   - Change default password immediately
   - Logout when not in use
   - Don't share admin credentials

## 🚧 Upcoming Features

- [ ] CSV export for orders
- [ ] Bulk order actions
- [ ] Email notifications
- [ ] Advanced filtering (date range, amount range)
- [ ] Customer management section
- [ ] Product inventory management
- [ ] Sales reports generation
- [ ] Dashboard widgets customization
- [ ] Multi-admin support with roles
- [ ] Activity audit log

## 🐛 Troubleshooting

### Issue: Cannot login
- **Solution**: Check credentials, ensure server is running

### Issue: No orders showing
- **Solution**: Check database connection, verify orders exist in database

### Issue: Charts not loading
- **Solution**: Check console for errors, ensure Chart.js is loaded

### Issue: Actions not working
- **Solution**: Check admin session, try refreshing the page

## 📞 Support

For issues or questions:
- Check logs in console
- Review error messages
- Contact development team

---

**Version**: 1.0.0  
**Last Updated**: October 2025
**Status**: ✅ Production Ready
