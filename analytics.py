class DefectAnalyzer:
    WALL_THICKNESS_MM = 12.0
    
    @classmethod
    def analyze_defect(cls, defect_type, depth_mm, length_mm, width_mm=None):
        if defect_type.lower() == "коррозия":
            depth_ratio = depth_mm / cls.WALL_THICKNESS_MM
            risk_score = min(100, (depth_ratio * 100) + (length_mm / 100))
            if depth_ratio >= 0.8:
                return "КРИТИЧЕСКИЙ", round(risk_score, 2), "НЕМЕДЛЕННЫЙ ремонт! Замена участка трубы."
            elif depth_ratio >= 0.5:
                return "ВЫСОКИЙ", round(risk_score, 2), "Плановый ремонт в течение 3 месяцев."
            elif depth_ratio >= 0.2:
                return "СРЕДНИЙ", round(risk_score, 2), "Мониторинг раз в 3 месяца."
            else:
                return "НИЗКИЙ", round(risk_score, 2), "Плановое наблюдение."
        elif defect_type.lower() == "трещина":
            risk_score = min(100, (length_mm / 50) * 100)
            if length_mm > 100:
                return "КРИТИЧЕСКИЙ", round(risk_score, 2), "НЕМЕДЛЕННЫЙ ремонт. Требуется шурфовка."
            elif length_mm > 50:
                return "ВЫСОКИЙ", round(risk_score, 2), "Ремонт в течение 1 месяца."
            elif length_mm > 20:
                return "СРЕДНИЙ", round(risk_score, 2), "Мониторинг раз в месяц."
            else:
                return "НИЗКИЙ", round(risk_score, 2), "Плановое наблюдение."
        elif defect_type.lower() == "вмятина":
            depth_ratio = depth_mm / cls.WALL_THICKNESS_MM
            risk_score = min(100, (depth_ratio * 100) + ((width_mm or depth_mm) / 200))
            if depth_mm > 10:
                return "ВЫСОКИЙ", round(risk_score, 2), "Ремонт с заменой изоляции."
            elif depth_mm > 5:
                return "СРЕДНИЙ", round(risk_score, 2), "Мониторинг и контроль давления."
            else:
                return "НИЗКИЙ", round(risk_score, 2), "Наблюдение в плановом порядке."
        else:
            return "СРЕДНИЙ", 50, "Требуется дополнительная диагностика"