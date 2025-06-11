# RTX Log - June 9, 2025
**Multi-User Testing Strategy for Dual LLM Queue System**

## Testing Objective
Simulate lab environment with multiple students using different browser tabs to validate:
- Queue management with concurrent users
- Two-phase processing efficiency  
- Real-time status updates across multiple sessions
- Performance under load (target: 30s per student)

## Multi-User Test Plan

### Browser Tab Simulation Setup
1. **Tab 1**: Student "23112001" - Submit audio file
2. **Tab 2**: Student "23112002" - Submit audio file  
3. **Tab 3**: Student "23112003" - Submit audio file
4. **Tab 4**: Queue Monitor - Watch real-time statistics
5. **Tab 5**: Admin Panel - Monitor system performance

### Test Scenarios

#### Scenario A: Sequential Submission (Baseline)
- Submit files one by one with 30-second intervals
- Measure individual processing times
- Validate queue position updates

#### Scenario B: Rapid Batch Submission (Lab Simulation)
- Submit 5-10 files within 2 minutes (simulating students in lab)
- Monitor STT batch formation (target: 10 students per batch)
- Track phase switching behavior

#### Scenario C: Mixed Timing (Realistic)
- Stagger submissions over 5-10 minutes
- Some students submit early, others late
- Validate queue handles mixed arrival patterns

## Test Data Preparation Required
