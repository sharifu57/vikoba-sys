# VikobaSys - Contribution Recording System Documentation

## Overview

The Contribution Recording System is a comprehensive solution for managing member contributions in the VikobaSys application. It supports both single contribution recording and bulk uploading via Excel files, making it easy to track and manage contributions efficiently.

## Features

### 1. **Single Contribution Recording**

- Record individual member contributions one at a time
- Support for multiple payment methods (Mobile Money, Cash, Bank Transfer, Check)
- Track payment references and add remarks
- Real-time balance calculation and status updates

### 2. **Bulk Upload**

- Upload multiple contributions via Excel file
- Drag-and-drop file upload interface
- Excel template download for reference
- Detailed error reporting for failed rows
- Progress tracking during upload

### 3. **Contribution Tracking**

- View all contributions in a organized table
- Filter by member name, member ID, status, and contribution period
- Summary statistics showing:
  - Total expected contributions
  - Total collected amount
  - Outstanding balance
  - Collection rate percentage
- Member status breakdown (Completed, Partial, Pending)

### 4. **Contribution Periods**

- Manage multiple contribution periods (e.g., January 2024, February 2024)
- Each period has an expected contribution amount
- Automatic period matching based on date ranges

## Backend Architecture

### DTOs (Data Transfer Objects)

#### RecordContributionRequest

Used for recording a single contribution via API.

```java
{
  "groupMemberId": 1,
  "contributionPeriodId": 1,
  "paidAmount": 50000,
  "paymentMethod": "Mobile Money",
  "paymentReference": "TXN123456",
  "remarks": "January 2024 contribution"
}
```

#### BulkContributionRequest

Used for bulk upload operations.

```java
{
  "groupId": 1,
  "contributions": [
    {
      "memberIdentifier": "MEM001",
      "contributionPeriod": "2024-01",
      "paidAmount": 50000,
      "paymentMethod": "Mobile Money",
      "paymentReference": "TXN123456",
      "remarks": "January 2024"
    }
  ],
  "remarks": "Bulk upload batch"
}
```

#### BulkContributionResult

Returns the result of a bulk upload operation.

```java
{
  "totalRows": 15,
  "successCount": 13,
  "failureCount": 2,
  "summary": "Processed 15 rows: 13 successful, 2 failed",
  "status": "PARTIAL",
  "failedRows": [
    {
      "rowNumber": 5,
      "memberIdentifier": "UNKNOWN",
      "errorMessage": "Member not found"
    }
  ]
}
```

### API Endpoints

#### Record Single Contribution

```
POST /api/contributions/record
Content-Type: application/json

{
  "groupMemberId": 1,
  "contributionPeriodId": 1,
  "paidAmount": 50000,
  "paymentMethod": "Mobile Money",
  "paymentReference": "TXN123456",
  "remarks": "January 2024 contribution"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Contribution recorded successfully.",
  "data": {
    "id": 1,
    "groupMemberId": 1,
    "contributionPeriodId": 1,
    "expectedAmount": 50000,
    "paidAmount": 50000,
    "balance": 0,
    "status": "PAID",
    "paidAt": "2024-01-15T10:30:00"
  }
}
```

#### Bulk Upload Contributions

```
POST /api/contributions/bulk-upload
Content-Type: multipart/form-data

Parameters:
- groupId: Long (required)
- file: MultipartFile (required) - Excel or CSV file
```

**Response:**

```json
{
  "status": "success",
  "message": "Bulk contribution upload processed.",
  "data": {
    "totalRows": 15,
    "successCount": 13,
    "failureCount": 2,
    "summary": "Processed 15 rows: 13 successful, 2 failed",
    "status": "PARTIAL",
    "failedRows": [...]
  }
}
```

#### Get Active Contribution Periods

```
GET /api/contributions/periods?groupId=1
```

**Response:**

```json
{
  "status": "success",
  "message": "Contribution periods retrieved successfully.",
  "data": [
    {
      "id": 1,
      "contributionTypeName": "Weekly Contribution",
      "periodStart": "2024-01-01",
      "periodEnd": "2024-01-31",
      "expectedAmount": 50000,
      "status": "OPEN",
      "displayText": "January 2024"
    }
  ]
}
```

#### Get All Contributions for Group

```
GET /api/contributions/group/{groupId}?status=PENDING&periodId=1
```

**Parameters:**

- `status`: Optional filter (PENDING, PAID, PARTIAL)
- `periodId`: Optional contribution period filter

**Response:** Returns array of ContributionDetailResponse objects

#### Get Member Contribution History

```
GET /api/contributions/member/{groupMemberId}
```

**Response:** Returns array of ContributionDetailResponse objects for that member

#### Get Contribution Summary

```
GET /api/contributions/group/{groupId}/summary
```

**Response:**

```json
{
  "status": "success",
  "message": "Contribution summary retrieved successfully.",
  "data": {
    "totalExpected": 500000,
    "totalPaid": 450000,
    "totalBalance": 50000,
    "collectionRate": 90,
    "membersCompleted": 8,
    "membersPartial": 1,
    "membersPending": 1,
    "totalMembers": 10
  }
}
```

#### Download Excel Template

```
GET /api/contributions/template/download
```

**Response:** Binary Excel file with template structure

#### Update Contribution

```
PUT /api/contributions/{contributionId}
Content-Type: application/json

{
  "groupMemberId": 1,
  "contributionPeriodId": 1,
  "paidAmount": 60000,
  "paymentMethod": "Mobile Money",
  "paymentReference": "TXN123456",
  "remarks": "Updated contribution"
}
```

## Frontend Components

### Contributions Page Structure

#### 1. Overview Tab

- Summary statistics (Expected, Collected, Outstanding, Collection Rate)
- Member status cards (Completed, Partial, Pending)
- Contribution table with advanced filtering
- Search by member name or ID
- Filter by status and period

#### 2. Record Single Tab

- Member selection dropdown
- Period selection dropdown
- Amount input with validation
- Payment method selection
- Payment reference input
- Remarks textarea
- Tips panel with best practices

#### 3. Bulk Upload Tab

- Drag-and-drop file upload area
- File selection with file browser
- Template download button
- Upload remarks textarea
- Progress bar during upload
- Results display with success/failure summary
- Failed rows detailed error messages

## Excel Template Format

The Excel template downloaded from the application follows this structure:

| Column A                 | Column B                      | Column C    | Column D       | Column E          | Column F             |
| ------------------------ | ----------------------------- | ----------- | -------------- | ----------------- | -------------------- |
| Member ID/Account Number | Contribution Period (YYYY-MM) | Paid Amount | Payment Method | Payment Reference | Remarks              |
| 1                        | 2024-01                       | 50000       | Mobile Money   | TXN12345          | January contribution |
| MEM002                   | 2024-01                       | 30000       | Cash           | CASH001           | Partial payment      |

**Important Notes:**

- Column B should be in YYYY-MM format (e.g., 2024-01 for January 2024)
- Column A can be member ID (numeric) or account number
- Column C (amount) should be numeric value
- Column D should match defined payment methods
- Rows are processed sequentially; failures don't stop processing

## Usage Examples

### Recording a Single Contribution

1. Navigate to Finance → Contributions
2. Click on "Record Single" tab
3. Select member from dropdown
4. Select contribution period
5. Enter paid amount
6. Select payment method
7. (Optional) Add payment reference and remarks
8. Click "Record Contribution"

### Bulk Uploading Contributions

1. Navigate to Finance → Contributions
2. Click on "Bulk Upload" tab
3. Click "Download Template" to get the Excel template
4. Fill in the template with contribution data
5. Save the file
6. Either:
   - Click to browse and select file, or
   - Drag and drop file into upload area
7. (Optional) Add upload remarks
8. Click "Upload & Process"
9. Review results and error details

### Viewing Contribution Summary

1. Navigate to Finance → Contributions
2. The overview tab shows:
   - Total expected contributions
   - Total collected amount
   - Outstanding balance
   - Collection rate
   - Member status breakdown

### Filtering Contributions

1. On the Contributions List tab:
2. Use search box to find by member name or ID
3. Use Status dropdown to filter by payment status
4. Use Period dropdown to filter by contribution period
5. Results update in real-time

## Status Meanings

- **PAID**: Member has paid the full expected contribution amount
- **PARTIAL**: Member has paid part of the expected contribution
- **PENDING**: Member has not made any contribution yet

## Error Handling

### Common Errors

| Error                                   | Cause                            | Solution                                                   |
| --------------------------------------- | -------------------------------- | ---------------------------------------------------------- |
| "Member not found"                      | Member ID doesn't exist in group | Verify member ID is correct                                |
| "Contribution period not found"         | Period doesn't exist             | Ensure period is in YYYY-MM format or select from dropdown |
| "Paid amount must be greater than zero" | Amount entered is 0 or negative  | Enter a positive amount                                    |
| "Invalid amount format"                 | Non-numeric value in bulk upload | Ensure all amounts are numbers                             |

### Bulk Upload Error Reporting

Failed rows are reported with:

- Row number in Excel file
- Member identifier that caused the error
- Specific error message
- Option to correct and retry

## Data Validation

### Single Contribution

- Member ID must exist and belong to the group
- Contribution period must be valid and active
- Paid amount must be > 0
- Payment method must be from predefined list

### Bulk Upload

- File must be Excel (.xlsx, .xls) or CSV
- File size must be < 10MB
- Each row validated individually
- Failed rows don't prevent processing of other rows

## Integration with Other Modules

### Member360

- Views contribution history for members
- Shows contribution status in member profile

### Dividend Module

- Uses contribution data to calculate dividend eligibility
- May restrict dividend access for members with PENDING contributions

### Loan Module

- May require full contribution payments before loan approval
- Tracks contribution payment history for credit scoring

## Troubleshooting

### Contributions Not Saving

- Check that all required fields are filled
- Verify member and period exist
- Check application logs for database errors

### Bulk Upload Too Slow

- Very large files (>5MB) may take time
- Consider splitting into multiple smaller batches
- Check browser console for performance issues

### Excel Template Not Opening

- Verify file format is .xlsx (not .xls or .csv)
- Try opening with Microsoft Excel or LibreOffice
- If corrupted, download template again

## Performance Considerations

- Bulk uploads process up to 10MB files
- Large uploads may take several seconds
- Progress bar provides visual feedback
- Failed rows don't affect successful rows
- Database uses indexed queries for filtering

## Security

- All contribution endpoints require authentication
- Members can only view their own contributions (Member360)
- Admin/Treasurer can view all group contributions
- Contributions are audit-logged for compliance

## Future Enhancements

Potential features for future releases:

- Automatic SMS/Email notifications for pending contributions
- Recurring contribution templates
- Contribution payment plans
- Integration with mobile money providers
- Contribution analytics and trends
- Automated bulk upload scheduling
- Contribution receipt generation and printing
