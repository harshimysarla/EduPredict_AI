"""Generate placeholder portal student datasets (student3, student4).
Placeholders only - real records for these students come later. Their
structure matches the Samvidha-style schema so real data can be dropped in.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def theory(no, code, name, gp, creds, att, status="Completed", grade_marks=8, cat="CORE", stype="T"):
    c1 = 20 + grade_marks * 1
    aat = max(6, grade_marks)
    total = c1 + aat * 4
    grade = {10: "S", 9: "A+", 8: "A", 7: "B+", 6: "B", 5: "C"}[gp]
    return {
        "serialNumber": no, "courseCode": code, "courseName": name,
        "CIE1": c1, "AAT1_I": aat, "AAT1_II": aat, "CIE2": c1,
        "AAT2_I": aat, "AAT2_II": aat, "totalMarks": total,
        "credits": creds, "grade": grade, "gradePoint": gp, "status": status,
        "attendance": att, "courseType": stype, "courseCategory": cat,
    }


def lab(no, code, name, gp, creds, att, status="Completed"):
    w = [9 if gp >= 9 else 8 if gp >= 8 else 7] * 14
    exam = {10: 46, 9: 44, 8: 42, 7: 40}.get(gp, 40)
    total = round(sum(w) / 14 / 10 * 60 + exam / 50 * 40)
    grade = {10: "S", 9: "A+", 8: "A", 7: "B+", 6: "B"}[gp]
    return {
        "serialNumber": no, "courseCode": code, "courseName": name,
        **{f"week{i}": w[i - 1] for i in range(1, 15)},
        "examMarks": exam, "totalMarks": total, "credits": creds,
        "grade": grade, "gradePoint": gp, "status": status, "attendance": att,
    }


def att(no, code, name, pct, cat="CORE", ctype="T", conducted=40):
    attended = round(conducted * pct / 100, 1)
    status = "Satisfactory" if pct >= 75 else "Condonation" if pct >= 65 else "Shortage"
    return {
        "courseCode": code, "courseName": name, "courseType": ctype,
        "courseCategory": cat, "conducted": conducted, "attended": attended,
        "attendancePercentage": pct, "status": status,
    }


def gr(code, name, gp, creds, att, status="Completed"):
    grade = {10: "S", 9: "A+", 8: "A", 7: "B+", 6: "B", 5: "C", None: "-"}[gp]
    return {
        "courseCode": code, "courseName": name, "grade": grade,
        "gradePoint": gp, "status": status, "credits": creds,
        "attendancePercentage": att,
    }


def semester(sem, theory_rows, lab_rows, att_rows, gr_rows, sgpa, total_credits):
    return {
        "semester": sem,
        "theoryCourses": theory_rows,
        "labCourses": lab_rows,
        "attendance": att_rows,
        "gradeRecords": gr_rows,
        "semesterSummary": {"sgpa": sgpa, "totalCredits": total_credits,
                            "earnedCredits": total_credits if sgpa else 0,
                            "semesterNumber": sem},
    }


COMMON_DUE = [
    {"category": "FOUNDATION", "requiredCourseCount": 12, "registeredCourseCount": 12, "yetToBeRegistered": 0},
    {"category": "CORE", "requiredCourseCount": 30, "registeredCourseCount": 22, "yetToBeRegistered": 8},
    {"category": "PROFESSIONAL ELECTIVE", "requiredCourseCount": 4, "registeredCourseCount": 1, "yetToBeRegistered": 3},
    {"category": "OPEN ELECTIVE", "requiredCourseCount": 2, "registeredCourseCount": 0, "yetToBeRegistered": 2},
    {"category": "PROJECT WORK", "requiredCourseCount": 2, "registeredCourseCount": 0, "yetToBeRegistered": 2},
    {"category": "AUDIT", "requiredCourseCount": 3, "registeredCourseCount": 3, "yetToBeRegistered": 0},
    {"category": "VALUE ADDED", "requiredCourseCount": 2, "registeredCourseCount": 1, "yetToBeRegistered": 1},
    {"category": "FIELD PROJECT / INTERNSHIP", "requiredCourseCount": 2, "registeredCourseCount": 0, "yetToBeRegistered": 2},
    {"category": "DIP COURSES", "requiredCourseCount": 0, "registeredCourseCount": 0, "yetToBeRegistered": 0},
]

S1_THEORY = [
    theory(1, "AHSD02", "MATRICES AND CALCULUS", 8, 4, 80, grade_marks=8, cat="FOUNDATION"),
    theory(2, "AHSD07", "APPLIED PHYSICS", 7, 3, 72, grade_marks=7, cat="FOUNDATION"),
    theory(3, "ACSD01", "OBJECT ORIENTED PROGRAMMING", 6, 3, 66, grade_marks=6, cat="CORE"),
    theory(4, "AHSD06", "ENVIRONMENTAL SCIENCE", 6, 0, None, grade_marks=7, cat="AUDIT"),
]
S1_LAB = [
    lab(5, "AHSD09", "APPLIED PHYSICS LABORATORY", 9, 1, 90),
    lab(6, "ACSD02", "OBJECT ORIENTED PROGRAMMING WITH JAVA LABORATORY", 9, 2, 84),
]
S1_ATT = [
    att(0, "AHSD02", "MATRICES AND CALCULUS", 80, cat="FOUNDATION"),
    att(0, "AHSD07", "APPLIED PHYSICS", 72, cat="FOUNDATION"),
    att(0, "ACSD01", "OBJECT ORIENTED PROGRAMMING", 66, cat="CORE"),
    att(0, "AHSD09", "APPLIED PHYSICS LABORATORY", 90, cat="FOUNDATION", ctype="L", conducted=20),
    att(0, "ACSD02", "OBJECT ORIENTED PROGRAMMING WITH JAVA LABORATORY", 84, cat="CORE", ctype="L", conducted=22),
]
S1_GR = [
    gr("AHSD02", "MATRICES AND CALCULUS", 8, 4, 80),
    gr("AHSD07", "APPLIED PHYSICS", 7, 3, 72),
    gr("ACSD01", "OBJECT ORIENTED PROGRAMMING", 6, 3, 66),
    gr("AHSD09", "APPLIED PHYSICS LABORATORY", 9, 1, 90),
    gr("ACSD02", "OBJECT ORIENTED PROGRAMMING WITH JAVA LABORATORY", 9, 2, 84),
    gr("AHSD06", "ENVIRONMENTAL SCIENCE", 6, 0, None),
]

S2_THEORY = [
    theory(1, "AHSD01", "PROFESSIONAL COMMUNICATION", 8, 3, 78, grade_marks=8, cat="FOUNDATION"),
    theory(2, "AHSD08", "DIFFERENTIAL EQUATIONS AND VECTOR CALCULUS", 7, 4, 74, grade_marks=7, cat="FOUNDATION"),
    theory(3, "ACSD05", "ESSENTIALS OF PROBLEM SOLVING", 7, 3, 70, grade_marks=7, cat="CORE"),
    theory(4, "AEED01", "ELEMENTS OF ELECTRICAL AND ELECTRONICS ENGINEERING", 6, 3, 68, grade_marks=6, cat="CORE"),
]
S2_LAB = [
    lab(5, "AHSD04", "PROFESSIONAL COMMUNICATION LABORATORY", 9, 1, 86),
    lab(6, "ACSD06", "PROGRAMMING FOR PROBLEM SOLVING LABORATORY", 8, 2, 80),
]
S2_ATT = [
    att(0, "AHSD01", "PROFESSIONAL COMMUNICATION", 78, cat="FOUNDATION", conducted=30),
    att(0, "AHSD08", "DIFFERENTIAL EQUATIONS AND VECTOR CALCULUS", 74, cat="FOUNDATION"),
    att(0, "ACSD05", "ESSENTIALS OF PROBLEM SOLVING", 70, cat="CORE", conducted=37),
    att(0, "AEED01", "ELEMENTS OF ELECTRICAL AND ELECTRONICS ENGINEERING", 68, cat="CORE", conducted=50),
    att(0, "AHSD04", "PROFESSIONAL COMMUNICATION LABORATORY", 86, cat="FOUNDATION", ctype="L", conducted=20),
    att(0, "ACSD06", "PROGRAMMING FOR PROBLEM SOLVING LABORATORY", 80, cat="CORE", ctype="L", conducted=43),
]
S2_GR = [
    gr("AHSD01", "PROFESSIONAL COMMUNICATION", 8, 3, 78),
    gr("AHSD08", "DIFFERENTIAL EQUATIONS AND VECTOR CALCULUS", 7, 4, 74),
    gr("ACSD05", "ESSENTIALS OF PROBLEM SOLVING", 7, 3, 70),
    gr("AEED01", "ELEMENTS OF ELECTRICAL AND ELECTRONICS ENGINEERING", 6, 3, 68),
    gr("AHSD04", "PROFESSIONAL COMMUNICATION LABORATORY", 9, 1, 86),
    gr("ACSD06", "PROGRAMMING FOR PROBLEM SOLVING LABORATORY", 8, 2, 80),
]

S3_THEORY = [
    theory(1, "ACSD08", "DATA STRUCTURES", 8, 3, 82, status="Registered", cat="CORE"),
    theory(2, "ACSD09", "OPERATING SYSTEMS", 6, 3, 68, status="Registered", grade_marks=6, cat="CORE"),
    theory(3, "AITD01", "MATHEMATICS FOR COMPUTING", 7, 3, 76, status="Registered", grade_marks=7, cat="FOUNDATION"),
    theory(4, "ACSD19", "DATA MINING AND MACHINE LEARNING", 5, 4, 62, status="Registered", grade_marks=5, cat="CORE"),
]
S3_LAB = [
    lab(5, "ACSD26", "ARTIFICIAL INTELLIGENCE LABORATORY", 6, 1, 60),
    lab(6, "ACSD27", "CLOUD APPLICATION DEVELOPMENT LABORATORY", 8, 1, 88),
]
S3_ATT = [
    att(0, "ACSD08", "DATA STRUCTURES", 82, cat="CORE"),
    att(0, "ACSD09", "OPERATING SYSTEMS", 68, cat="CORE", conducted=34),
    att(0, "AITD01", "MATHEMATICS FOR COMPUTING", 76, cat="FOUNDATION", conducted=42),
    att(0, "ACSD19", "DATA MINING AND MACHINE LEARNING", 62, cat="CORE", conducted=28),
    att(0, "ACSD26", "ARTIFICIAL INTELLIGENCE LABORATORY", 60, cat="CORE", ctype="L", conducted=17),
    att(0, "ACSD27", "CLOUD APPLICATION DEVELOPMENT LABORATORY", 88, cat="CORE", ctype="L", conducted=12),
]
S3_GR = [
    gr("ACSD08", "DATA STRUCTURES", None, 3, 82, status="Registered"),
    gr("ACSD09", "OPERATING SYSTEMS", None, 3, 68, status="Registered"),
    gr("AITD01", "MATHEMATICS FOR COMPUTING", None, 3, 76, status="Registered"),
    gr("ACSD19", "DATA MINING AND MACHINE LEARNING", None, 4, 62, status="Registered"),
    gr("ACSD26", "ARTIFICIAL INTELLIGENCE LABORATORY", None, 1, 60, status="Registered"),
    gr("ACSD27", "CLOUD APPLICATION DEVELOPMENT LABORATORY", None, 1, 88, status="Registered"),
]


def build(username, name, roll, section, cgpa, prev_sgpa, prev_cgpa, sgpa1, sgpa2):
    return {
        "username": username, "password": "demo123",
        "studentId": roll, "name": name, "rollNumber": roll,
        "branch": "COMPUTER SCIENCE AND ENGINEERING", "regulation": "BT23",
        "section": section, "year": 2, "currentSemester": 3,
        "cgpa": cgpa, "previousSgpa": prev_sgpa, "previousSemesterCgpa": prev_cgpa,
        "dateOfAdmission": "2024-08-01", "placeholder": True,
        "profile": {
            "name": name, "rollNumber": roll, "studentId": roll,
            "branch": "COMPUTER SCIENCE AND ENGINEERING", "regulation": "BT23",
            "section": section, "year": 2, "currentSemester": 3,
            "cgpa": cgpa, "previousSgpa": prev_sgpa, "previousSemesterCgpa": prev_cgpa,
            "dateOfAdmission": "2024-08-01",
        },
        "semesterRecords": [
            semester(1, S1_THEORY, S1_LAB, S1_ATT, S1_GR, sgpa1, 13),
            semester(2, S2_THEORY, S2_LAB, S2_ATT, S2_GR, sgpa2, 16),
            semester(3, S3_THEORY, S3_LAB, S3_ATT, S3_GR, None, 15),
        ],
        "overallSummary": {"cgpa": cgpa, "totalCredits": 29, "earnedCredits": 29,
                           "programTotalCredits": 160, "currentSemester": 3},
        "currentSemesterCourses": [
            {"courseCode": "ACSD08", "courseName": "DATA STRUCTURES", "courseType": "T", "courseCategory": "CORE", "credits": 3, "attendance": 82, "status": "Satisfactory"},
            {"courseCode": "ACSD09", "courseName": "OPERATING SYSTEMS", "courseType": "T", "courseCategory": "CORE", "credits": 3, "attendance": 68, "status": "Condonation"},
            {"courseCode": "AITD01", "courseName": "MATHEMATICS FOR COMPUTING", "courseType": "T", "courseCategory": "FOUNDATION", "credits": 3, "attendance": 76, "status": "Satisfactory"},
            {"courseCode": "ACSD19", "courseName": "DATA MINING AND MACHINE LEARNING", "courseType": "T", "courseCategory": "CORE", "credits": 4, "attendance": 62, "status": "Shortage"},
            {"courseCode": "ACSD26", "courseName": "ARTIFICIAL INTELLIGENCE LABORATORY", "courseType": "L", "courseCategory": "CORE", "credits": 1, "attendance": 60, "status": "Shortage"},
            {"courseCode": "ACSD27", "courseName": "CLOUD APPLICATION DEVELOPMENT LABORATORY", "courseType": "L", "courseCategory": "CORE", "credits": 1, "attendance": 88, "status": "Satisfactory"},
        ],
        "coursesDue": COMMON_DUE,
    }


def main():
    s3 = build("24951A05B2", "DEMO STUDENT THREE (PLACEHOLDER)", "24951A05B2",
               "B", 6.9, 7.1, 7.0, 8.0, 6.4)
    s4 = build("24951A05B4", "DEMO STUDENT FOUR (PLACEHOLDER)", "24951A05B4",
               "D", 8.6, 8.9, 8.7, 8.8, 8.5)
    for fname, data in [("student3.json", s3), ("student4.json", s4)]:
        path = os.path.join(HERE, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("wrote", path)


if __name__ == "__main__":
    main()