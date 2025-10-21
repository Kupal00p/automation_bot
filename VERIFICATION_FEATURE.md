# 🛡️ Admin Verification System - User Guide

## Overview

The admin dashboard now includes a comprehensive verification system that allows you to review and approve/reject customer identity verifications and payment proofs.

## Features Added

### 1. **Enhanced Order Details Modal**

When you click on an order, you'll see:

#### **Customer Information Section**
- Full name and contact details
- Delivery address
- Customer tier (Regular/VIP/Premium)
- Total orders history

#### **Verification Section** (if verification required)
Shows detailed verification information including:

**For ID Verification:**
- ✅ Valid ID image (clickable to view full size)
- ✅ Selfie with ID image (clickable to view full size)
- ID type (e.g., Driver's License, Passport)
- Verification status with color coding:
  - 🟡 Yellow = Pending/Under Review
  - 🟢 Green = Verified
  - 🔴 Red = Rejected
  - 🔵 Blue = Under Review

**For Upfront Payment:**
- Payment amount (10% of total)
- Payment method (GCash/Maya/Bank Transfer)
- Payment proof screenshot (clickable to view full size)

#### **Interactive Features:**
1. **Click any verification image** → Opens full-size modal
2. **Approve button** → Confirms order and notifies customer
3. **Reject button** → Prompts for reason, notifies customer to resubmit

### 2. **Image Viewing**

Click on any ID, selfie, or payment proof image to:
- View in full screen with black background
- Click outside or X button to close
- Zoom and inspect details clearly

### 3. **Order Summary**

Improved layout showing:
- Subtotal
- Shipping fee
- Discounts (if any)
- **Upfront paid amount** (highlighted in blue)
- **Total amount** (bold, large font)
- **Remaining balance** for COD (if applicable, shown in orange)

## How to Use

### **Approving ID Verification**

1. Navigate to **Orders** section
2. Click the **eye icon** on an order requiring verification
3. Review the **Verification Required** section
4. Check both images:
   - Valid ID should be clear and readable
   - Selfie should show customer holding the ID
   - Face should match ID photo
5. Click **Approve Verification**
6. Confirm the approval
7. ✅ Order is automatically confirmed and customer receives notification

### **Rejecting Verification**

1. In order details, review verification images
2. If images are unclear, don't match, or suspicious:
3. Click **Reject Verification**
4. Enter specific reason (e.g., "ID photo is blurry", "Face doesn't match ID")
5. Customer receives rejection notice and can resubmit

### **Approving Payment Verification**

1. Open order with upfront payment verification
2. Review payment proof screenshot
3. Verify:
   - Amount matches 10% of order total
   - Payment method matches
   - Screenshot shows successful transaction
4. Click **Approve Verification**
5. Order confirmed, remaining balance marked for COD

### **Confirming Regular Orders**

Orders without verification requirements:
- Simply click **Confirm Order** button
- Customer receives confirmation immediately
- Order moves to processing

## Order Status Flow

```
Customer Places Order
         ↓
[Verification Required?]
         ↓
    Yes → Customer submits ID/Payment
         ↓
    Admin Reviews in Dashboard
         ↓
    [Approve] → Order Confirmed ✅
         ↓
    [Reject] → Customer Resubmits 🔄
         ↓
    Final Approval → Processing
         ↓
    Shipped → Delivered
```

## Verification Statuses

| Status | Color | Meaning | Action Required |
|--------|-------|---------|-----------------|
| **Pending** | 🟡 Yellow | Waiting for customer | Wait for submission |
| **Under Review** | 🔵 Blue | Customer submitted | Review & approve/reject |
| **Verified** | 🟢 Green | Approved by admin | Can confirm order |
| **Rejected** | 🔴 Red | Failed verification | Wait for resubmission |

## Best Practices

### ✅ **DO:**
- Check ID expiration date
- Verify face matches photo
- Ensure ID is government-issued
- Check payment amount matches exactly
- Provide specific rejection reasons
- Respond within 1-2 hours

### ❌ **DON'T:**
- Approve blurry or unclear images
- Accept IDs where name doesn't match
- Approve if face is covered in selfie
- Accept partial payment proofs
- Approve suspicious documents

## Common Rejection Reasons

**For ID Verification:**
- "ID image is too blurry, please upload a clearer photo"
- "Face in selfie doesn't match ID photo"
- "ID appears to be expired, please use valid ID"
- "Selfie doesn't show you holding the ID clearly"
- "Name on ID doesn't match order name"

**For Payment Verification:**
- "Payment amount doesn't match required upfront (₱X,XXX.XX)"
- "Screenshot doesn't show transaction reference number"
- "Payment proof appears altered or edited"
- "Transaction date doesn't match submission time"

## Verification Workflow Example

### Scenario: ₱75,000 COD Order

1. **Order Placed** (10:00 AM)
   - Samsung Galaxy S24 Ultra
   - Total: ₱75,040
   - Payment: COD
   - Verification Required: ✅ Yes

2. **Customer Chooses ID Verification** (10:05 AM)
   - Uploads Driver's License
   - Uploads selfie with ID
   - Status: Under Review

3. **Admin Reviews** (10:30 AM)
   - Opens order details
   - Clicks ID image → Views full screen
   - Clicks selfie → Views full screen
   - Verifies match ✅

4. **Admin Approves** (10:32 AM)
   - Clicks "Approve Verification"
   - Order auto-confirmed
   - Customer notified

5. **Order Processing** (10:35 AM)
   - Prepare items
   - Arrange delivery
   - Update tracking

## Technical Details

### API Endpoints Used:
- `GET /admin/api/orders/<id>` - Get order with verification
- `POST /admin/api/verifications/<order_id>/approve` - Approve
- `POST /admin/api/verifications/<order_id>/reject` - Reject

### Data Retrieved:
```json
{
  "verification": {
    "verification_type": "id_verification",
    "verification_status": "under_review",
    "id_image_url": "https://...",
    "selfie_image_url": "https://...",
    "id_type": "Driver's License",
    "submitted_at": "2025-10-17T10:05:00"
  }
}
```

## Security Considerations

1. **Image Privacy**: Verification images contain sensitive PII
2. **Secure Storage**: Images should be stored securely
3. **Access Control**: Only logged-in admins can view
4. **Audit Trail**: All approvals/rejections are logged
5. **Data Retention**: Follow GDPR/privacy laws

## Troubleshooting

### Issue: Can't see verification images
**Solution**: Check if customer has submitted verification. Status should be "under_review"

### Issue: Images not loading
**Solution**: Check image URLs in database, verify hosting service is accessible

### Issue: Approve button not working
**Solution**: Ensure verification status is "under_review" or "pending"

### Issue: Customer didn't receive notification
**Solution**: Check messenger_id in database, verify notification service is running

## Future Enhancements

- [ ] Bulk verification approval
- [ ] AI-powered ID validation
- [ ] Face matching algorithms
- [ ] Verification history per customer
- [ ] Risk scoring system
- [ ] Automated approval for trusted customers

---

**Last Updated**: October 2025  
**Version**: 1.0.0
