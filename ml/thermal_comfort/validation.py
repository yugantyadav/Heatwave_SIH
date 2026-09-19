import json
from typing import List, Dict, Any

NWS_REFERENCE_TABLE = {
    # Temperature (°C), RH (%) -> Expected Heat Index (°C)
    # Based on NWS published tables
    (20, 30): 20, (20, 50): 20, (20, 70): 20, (20, 90): 21,
    (25, 30): 25, (25, 50): 25, (25, 70): 26, (25, 90): 27,
    (30, 30): 30, (30, 50): 30, (30, 70): 33, (30, 90): 36,
    (35, 30): 35, (35, 50): 38, (35, 70): 44, (35, 90): 50,
    (40, 30): 40, (40, 50): 45, (40, 70): 53, (40, 90): 60,
    (45, 30): 47, (45, 50): 53, (45, 70): 61, (45, 90): 70,
}

def run_validation_tests() -> List[Dict[str, Any]]:
    """Run validation against NWS reference tables."""
    from ml.thermal_comfort.indices import heat_index_rothfusz
    
    results = []
    for (temp, rh), expected in NWS_REFERENCE_TABLE.items():
        calculated = heat_index_rothfusz(temp, rh)
        result = {
            "temperature_c": temp,
            "relative_humidity": rh,
            "calculated_hi": calculated,
            "expected_hi": expected,
            "error": abs(calculated - expected) if calculated else None,
            "within_tolerance": abs(calculated - expected) <= 3.0 if calculated else False
        }
        results.append(result)
    
    passed = sum(1 for r in results if r["within_tolerance"])
    total = len(results)
    
    summary = {
        "total_tests": total,
        "passed": passed,
        "failed": total - passed,
        "success_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A",
        "reference": "NWS Heat Index Tables (Rothfusz 1990)"
    }
    
    return {"results": results, "summary": summary}

def print_validation_report():
    """Print a formatted validation report."""
    report = run_validation_tests()
    print("=" * 60)
    print("PYTHERMALCOMFORT VALIDATION REPORT")
    print("=" * 60)
    print(f"Reference: {report['summary']['reference']}")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {report['summary']['success_rate']}")
    print("=" * 60)
    for r in report["results"]:
        status = "✓" if r["within_tolerance"] else "✗"
        print(f"{status} T={r['temperature_c']}°C RH={r['relative_humidity']}% "
              f"Calculated={r['calculated_hi']} Expected={r['expected_hi']} "
              f"Error={r['error']:.1f}")
    print("=" * 60)
    return report

if __name__ == "__main__":
    print_validation_report()