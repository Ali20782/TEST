# Milestone 1: Dataset Validation Report

**Generated:** 2025-12-13 01:29:18

---

## Dataset: BPI_2012

### Basic Statistics

- **Total Events:** 262,200
- **Total Cases:** 13,087
- **Unique Activities:** 24
- **Date Range:** 2011-10-01 to 2012-03-14
- **Process Discovery:** ✅ Success

### Process Variants

**Total Variants:** 4366

**Top 5 Variants:**

1. `A_SUBMITTED → A_PARTLYSUBMITTED → A_DECLINED...`
   - Cases: 3429 (26.2%)

2. `A_SUBMITTED → A_PARTLYSUBMITTED → W_Afhandelen leads → W_Afhandelen leads → A_DECLINED → W_Afhandele...`
   - Cases: 1872 (14.3%)

3. `A_SUBMITTED → A_PARTLYSUBMITTED → W_Afhandelen leads → W_Afhandelen leads → W_Afhandelen leads → W_A...`
   - Cases: 271 (2.1%)

4. `A_SUBMITTED → A_PARTLYSUBMITTED → W_Afhandelen leads → W_Afhandelen leads → A_PREACCEPTED → W_Comple...`
   - Cases: 209 (1.6%)

5. `A_SUBMITTED → A_PARTLYSUBMITTED → A_PREACCEPTED → W_Completeren aanvraag → W_Completeren aanvraag → ...`
   - Cases: 160 (1.2%)

### Performance Metrics

- **Average Case Duration:** 8 days, 14 hours
- **Min Duration:** 1.00 sec
- **Max Duration:** 137 days, 4 hours

### Rework Analysis

- **Cases with Rework:** 9658 (73.8%)

### Bottleneck Activities

**Top 3 Activities by Average Time to Next Activity:**

1. **W_Nabellen offertes**: 1 day, 6 hours average
2. **W_Completeren aanvraag**: 16 hours, 42 min average
3. **W_Wijzigen contractgegevens**: 15 hours, 45 min average

### Data Quality

✅ **No quality issues detected**

---

## Dataset: BPI_2017

### Basic Statistics

- **Total Events:** 1,202,267
- **Total Cases:** 31,509
- **Unique Activities:** 26
- **Date Range:** 2016-01-01 to 2017-02-01
- **Process Discovery:** ✅ Success

### Process Variants

**Total Variants:** 15930

**Top 5 Variants:**

1. `A_Create Application → A_Submitted → W_Handle leads → W_Handle leads → W_Complete application → A_Co...`
   - Cases: 1056 (3.4%)

2. `A_Create Application → W_Complete application → W_Complete application → A_Concept → A_Accepted → O_...`
   - Cases: 1021 (3.2%)

3. `A_Create Application → A_Submitted → W_Handle leads → W_Handle leads → W_Complete application → A_Co...`
   - Cases: 734 (2.3%)

4. `A_Create Application → A_Submitted → W_Handle leads → W_Handle leads → W_Complete application → A_Co...`
   - Cases: 451 (1.4%)

5. `A_Create Application → A_Submitted → W_Handle leads → W_Handle leads → W_Complete application → A_Co...`
   - Cases: 332 (1.1%)

### Performance Metrics

- **Average Case Duration:** 21 days, 21 hours
- **Min Duration:** 3 min
- **Max Duration:** 286 days, 1 hour

### Rework Analysis

- **Cases with Rework:** 31509 (100.0%)

### Bottleneck Activities

**Top 3 Activities by Average Time to Next Activity:**

1. **W_Personal Loan collection**: 18 days average
2. **W_Call after offers**: 2 days, 10 hours average
3. **O_Sent (online only)**: 2 days, 4 hours average

### Data Quality

✅ **No quality issues detected**

---

## Dataset: Synthetic_Invoice

### Basic Statistics

- **Total Events:** 1,242
- **Total Cases:** 200
- **Unique Activities:** 9
- **Date Range:** 2024-01-01 to 2024-04-11
- **Process Discovery:** ✅ Success

### Process Variants

**Total Variants:** 3

**Top 5 Variants:**

1. `Create Invoice → Validate Data → Auto-Approve → Send to Payment → Mark Complete...`
   - Cases: 112 (56.0%)

2. `Create Invoice → Validate Data → Manual Review → Request Correction → Manual Review → Approve → Send...`
   - Cases: 66 (33.0%)

3. `Create Invoice → Validate Data → Manual Review → Manager Approval → Approve → Send to Payment → Mark...`
   - Cases: 22 (11.0%)

### Performance Metrics

- **Average Case Duration:** 5 days, 5 hours
- **Min Duration:** 15 min
- **Max Duration:** 16 days, 5 hours

### Rework Analysis

- **Cases with Rework:** 66 (33.0%)

### Bottleneck Activities

**Top 3 Activities by Average Time to Next Activity:**

1. **Manager Approval**: 9 days, 5 hours average
2. **Request Correction**: 4 days, 4 hours average
3. **Manual Review**: 3 days average

### Data Quality

✅ **No quality issues detected**

---

## Summary

**Total Datasets Validated:** 3

**Ready for Next Phase:** ✅ Yes
