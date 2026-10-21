I found 383 file results and 10 meetings, with 3 unique processed items surfaced as most relevant. The important finding is that Data Platform - Daily 2026-10-20.loop does not itself define the KPI-to-source mapping. It says the BI Dashboard had just started and that you were assessing whether the available source contained enough information for an MVP. The concrete MVP definition is in PRD_Business_Dashboard_Workshop_MVP.docx.

1. MVP scope I would use

The MVP is explicitly Workshop only. Used Vehicles, New Vehicles, Marketing, Customer and Financials are later phases. The Workshop release is intended to prove the data model, KPI definitions, role-based visibility and dashboard experience.

For the first implementable Data Platform slice, I would separate the requirements into:

Core MVP
Workshop load & capacity
Technician utilisation
Appointment demand
Repair-order status
Multi-level aggregation
Drill-down/filtering
Data freshness/source health
Conditional MVP
Forecasted bottlenecks
Throughput & cycle time
No-show/cancellation
Revenue/margin proxy

These are marked Should, rather than Must, and some depend on data availability.

2. KPI → Source → Transformation

The PRD identifies logical source entities, but not physical iCar tables/columns or complete calculation formulas. So I would create the following mapping for architecture purposes, distinguishing documented transformations from transformations that still require business-definition validation.

KPI	Priority	Required source	Data Platform transformationBooked workload	Must	Appointments + repair orders	Normalise appointments/RO workload into workshop/day; aggregate booked workload by workshop/date
Available capacity	Must	Technician calendars/capacity	Standardise technician availability/capacity by workshop/day; aggregate available capacity
Load vs Capacity	Must	Booked workload + capacity	Join workload and capacity at workshop/day grain and compare them; foundation for overload indicators
Technician utilisation	Must	Technician master + time bookings + RO labour lines	Harmonise technician identity; associate booked/worked labour with technician/workshop/period and derive utilisation using the agreed semantic definition
Appointment demand	Must	Appointment Center + DMS appointments	Normalise appointment records; classify by day/slot/workshop/service type and aggregate demand
Repair-order status funnel	Must	DMS repair orders/statuses	Harmonise DMS statuses into a common status model; group/count repair orders by status
Throughput	Should	Repair orders + invoicing completion events	Identify completed work from the relevant completion event and aggregate completed ROs over the requested period
Cycle time	Should	Repair-order timestamps + invoicing completion events	Establish start/completion timestamps and calculate elapsed time per RO before period aggregation
No-show / cancellation	Should	Appointments + cancellation reasons where available	Normalise appointment outcome/status and aggregate cancellations/no-shows across permitted dimensions
Revenue / contribution proxy	Should	DMS invoicing + permitted finance data	Harmonise financial inputs and calculate the agreed revenue/contribution measure. Exact calculation is not specified in the PRD
Forecasted bottleneck	Should	Capacity model + forecasting data/service	Compare projected demand against available capacity. PRD allows initial rule-based flags; full forecasting isn't a prerequisite
Group/site/workshop KPI roll-up	Must	Multi-tenant hierarchy + KPI datasets	Map records to workshop → dealership → brand → country → group and aggregate using authorised hierarchy
Data freshness	Must	Data-pipeline observability	Expose refresh timestamp and source/feed health to the dashboard

The sources and dependencies above are explicitly identified by the PRD. It states, for example, that load/capacity depends on appointments, repair orders and technician calendars/capacity, utilisation on technician master, time bookings and RO labour lines, appointment demand on Appointment Center/DMS appointments, and cycle time on RO timestamps and invoicing completion events.

The overarching ingestion scope is likewise explicit:

DMS / Workshop systems → Data Platform

Repair orders
Labour lines
Statuses
Workshop events
Workshop capacity inputs

Appointment Center / DMS → Data Platform

Appointments
Cancellations
No-shows
Service type
Advisor/workshop dimensions.
3. What this means for the Data Platform

I would translate those requirements into this logical MVP data pipeline:

DMS / Workshop                   Appointment systems
       │                                │
       └──────────┐          ┌──────────┘
                  ▼          ▼
              RAW / INGESTION
                    │
                    ▼
          STANDARDISED ENTITIES
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   Repair Order  Appointment  Technician
   + Labour      + Outcome     + Capacity
        │           │            │
        └───────────┼────────────┘
                    ▼
              SEMANTIC MODEL
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
   Load/Capacity  Utilisation   Demand
   RO Status      Throughput    Cycle Time
                    │
                    ▼
              Business Dashboard


This aligns with the PRD requirement that the dashboard consume common KPIs and dimensions from the Data Platform/Semantic Layer, including capacity, utilisation, appointment, productivity and throughput.

4. The critical gap for your architecture assessment

This is where I think your comment in Data Platform - Daily 2026-10-20.loop becomes particularly important.

The document says you were assessing whether the BI Dashboard data source has enough information to implement the MVP.

We can now formulate that assessment much more precisely:

We don't need to ask "does the database contain enough data?"

We need to verify whether it contains these minimum data families:

Repair order

identifiers
workshop association
status
operational timestamps

Repair-order labour

RO association
technician association
booked/worked/invoiced labour information where available

Technician

technician identity
workshop/team association
availability/capacity/calendar

Appointment

appointment identity
date/time/slot
workshop
service type
status/outcome
cancellation/no-show where available

Organisation hierarchy

workshop
company/dealership
brand
group

Invoicing/completion information

completion/invoice event
timestamps
financial measures if W-09 is retained

The need for these entity families follows directly from the dependencies and sources specified for the Workshop requirements.

5. The most important distinction: KPI definition ≠ transformation specification

I would not yet treat the PRD as sufficient to build all transformations.

For example, it says Technician Utilisation, but doesn't provide an authoritative equation defining its numerator and denominator. Similarly, it requires cycle time, but does not define which exact source event represents the start of the cycle in every DMS. And revenue/margin proxy explicitly depends on available financial information without giving the calculation.

That's important because the PRD itself requires source-to-metric lineage, specifically tracing KPI values back to source entities and transformation logic. It also requires shared metric definitions in a reusable semantic layer rather than customer-specific dashboard calculations.

Therefore, the real MVP architecture deliverable should be:

Source → Entity → Field → Transformation → KPI → Dashboard

not merely:

Source → Dashboard

For example:

DMS
 ↓
Repair Order / Labour / Technician / Appointment
 ↓
Canonical Workshop entities
 ↓
Validated transformations
 ↓
Semantic KPIs
 ↓
QuickSight / Business Dashboard


That gives you a very precise next checkpoint: take the actual candidate source you mentioned in the 20 October daily and perform a field-by-field coverage assessment against these six source families. The result will tell you objectively which Workshop MVP KPIs are Ready / Partial / Blocked, instead of trying to reproduce the entire legacy reporting capability.