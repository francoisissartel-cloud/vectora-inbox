# Glossary — RAG LAI

# Long-Acting Injectable (LAI) — Canonical Definition

**Definition (strict):**  
A *Long-Acting Injectable (LAI)* is a **drug formulation administered by injection** (see `taxonomy/route_admin.csv`) that, by using a recognized **technology_type** (`tech_dds` or `tech_hle`), is **designed to provide a sustained, controlled, or extended therapeutic effect** over **weeks to months** **from a single injection** (or a scheduled series such as monthly/bi-monthly).

**Inclusion criteria**
- **Injectable route** only (e.g., IV, IM, SC, ID, intravitreal, intra-articular, intrathecal, intravesical, *surgical site instillation*, etc.).  
- Uses a **technology_family**:
  - `tech_dds` (Drug Delivery System): depot or formulation system that releases API over time (see `taxonomy/technology_family.csv`, families starting with `fam_depot_*`, `fam_liposome_*`, `fam_hydrogel_*`, `fam_nanosuspension`, `fam_emulsion`, etc.).
  - `tech_hle` (Half-Life Extension Strategy): molecular strategies extending systemic half-life **without a physical depot** (e.g., PEGylation, PASylation, Fc/albumin fusion, lipidation, XTEN, glyco-engineering, sequence engineering).
- Intended **duration** measured in days,  weeks or months (e.g., *q4w, q8w, q12w, 1- month, monthly, 2-month, 3-month, 6-month, yearly*).

**Exclusion criteria**
- **Implantable devices** (placed surgically under the skin or into a cavity and left in place) are **excluded** from LAI scope, even if they release a drug (use separate implant taxonomy if needed).
- **Gene or cell therapies** (non-injectable drug products in the conventional sense) are out of scope.
- Pure **IV infusions** that are not designed for long-acting exposure (no depot and no HLE) are excluded.

**Rationale for two technology types**
- **DDS (tech_dds)**: produces a **local depot** at/near the injection site, releasing API gradually.
- **HLE (tech_hle)**: **increases circulating half-life** (e.g., FcRn recycling, albumin binding), achieving long exposure without a depot.

**Operational guidance**
- Every drug record in Gold/curated **must** reference: `route_admin_id` + `technology_type_id`.  
- If `technology_type_id = tech_dds`, a `technology_family_id` from DDS families is expected.  
- If `technology_type_id = tech_hle`, a `technology_family_id` from HLE strategies is expected.  
- Metadata should include declared **dosing interval** (e.g., q4w) or textual duration claims ("2-month duration").

## Drug Delivery System (DDS)
Technology platform that controls the release, distribution, and elimination of pharmaceutical compounds.

## Half-Life Extension (HLE)
Strategies to increase the duration a drug remains active in the body, typically through protein engineering or conjugation.

## Depot Injection
Injectable formulation that creates a reservoir of drug at the injection site for sustained release.

## Microspheres
Spherical particles (1-1000 μm) used as drug carriers, often made from biodegradable polymers like PLGA.

## Bioavailability
The proportion of administered drug that reaches systemic circulation in active form.

## Pharmacokinetics (PK)
Study of drug absorption, distribution, metabolism, and excretion over time.

## Target Product Profile (TPP)
Document defining the desired characteristics of a drug product for specific indication and patient population.

## Controlled Release
Drug delivery system that releases active ingredient at predetermined rate over specific time period.

## Subcutaneous (SC)
Injection into tissue layer between skin and muscle, commonly used for LAI formulations.

## Parenteral
Administration of drugs by injection, bypassing the gastrointestinal tract (IV, IM, SC routes).

## In-situ Forming Depot
Liquid formulation that solidifies after injection to form sustained-release depot at injection site.

## Pivotal Trial
Phase III clinical trial designed to provide definitive evidence of efficacy for regulatory approval.

## Registrational Trial
Clinical trial conducted to support regulatory filing and drug approval (typically Phase III).

## Multivesicular Liposome (MVL)
Liposomal drug delivery system with multiple internal aqueous compartments for sustained release.

## Polymeric Microsphere
Spherical particles made from biodegradable polymers (e.g., PLGA) for controlled drug release.

## Prodrug
Inactive compound that is metabolized in the body to release the active drug, often used for depot formulations.