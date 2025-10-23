# Upgrade Notes - MyDebtReminder Bot

## Version 2.0 - Step-by-Step Debt Addition (October 23, 2025)

### Major Changes

#### Enhanced Add Debt Flow
The `/add_debt` command has been completely redesigned to provide a more user-friendly, step-by-step experience.

**Previous Behavior:**
- Users had to input all debt information in a single message with comma-separated values
- Format: `category,amount,due_date,description,recurrence`
- Example: `اجاره,2000000,2024-12-01,اجاره ماهانه آپارتمان,monthly`
- Error-prone and confusing for users

**New Behavior:**
- Interactive 5-step conversation flow
- Bot asks for each field separately:
  1. **Category** - Suggests common categories (rent, installment, utilities, etc.)
  2. **Amount** - Validates numeric input, accepts Persian/English numbers
  3. **Due Date** - Validates date format (YYYY-MM-DD)
  4. **Description** - Optional field, accepts "ندارد" or "-" to skip
  5. **Recurrence** - Interactive buttons for selection (one-time, monthly, weekly, yearly)

**Benefits:**
- ✅ More intuitive and user-friendly
- ✅ Better input validation at each step
- ✅ Clear progress indication (Step X of 5)
- ✅ Helpful examples and suggestions
- ✅ Can cancel at any time with `/cancel`
- ✅ Summary of entered data before final submission
- ✅ Supports both Persian and English number formats

### Technical Implementation

#### New Conversation States
```python
ADDING_DEBT_CATEGORY = 1
ADDING_DEBT_AMOUNT = 2
ADDING_DEBT_DATE = 3
ADDING_DEBT_DESCRIPTION = 4
ADDING_DEBT_RECURRENCE = 5
```

#### New Handler Functions
- `add_debt_start()` - Initiates the conversation, asks for category
- `add_debt_category()` - Processes category, asks for amount
- `add_debt_amount()` - Validates and processes amount, asks for date
- `add_debt_date()` - Validates date format, asks for description
- `add_debt_description()` - Processes description, shows recurrence buttons
- `add_debt_recurrence()` - Processes selection and saves the debt

#### Data Storage
User input is temporarily stored in `context.user_data` during the conversation:
- `debt_category`
- `debt_amount`
- `debt_due_date`
- `debt_description`

Data is cleared after successful debt creation or cancellation.

### User Experience Improvements

1. **Input Validation**
   - Empty category check
   - Numeric validation for amount (with comma/Persian comma support)
   - Positive amount validation
   - ISO date format validation
   - Helpful error messages with retry prompts

2. **Visual Feedback**
   - ✅ Checkmarks for completed steps
   - Progress indicators (Step X of 5)
   - Summary display before final submission
   - Persian translations for recurrence types

3. **Flexibility**
   - Optional description field
   - Multiple ways to skip description ("ندارد", "-", "نداره", "no", "none")
   - Cancel option at any step

### Updated Help Text
The `/help` command now reflects the new step-by-step process with clear instructions for each stage.

### Backward Compatibility
⚠️ **Breaking Change**: The old comma-separated input format is no longer supported. Users must use the new interactive flow.

### Migration Notes
No database migration required. This is purely a UI/UX change in how data is collected from users.

### Testing Recommendations
1. Test the complete flow from start to finish
2. Test cancellation at each step
3. Test invalid inputs (empty category, non-numeric amount, invalid date)
4. Test Persian and English number inputs
5. Test description skip options
6. Test all recurrence type buttons
7. Verify data is properly saved to database
8. Verify user_data is cleared after completion/cancellation

### Future Enhancements
Potential improvements for future versions:
- Add edit functionality for existing debts
- Support for Persian calendar (Jalali) dates
- Bulk debt import
- Debt templates for recurring expenses
- Category management (add/edit custom categories)
