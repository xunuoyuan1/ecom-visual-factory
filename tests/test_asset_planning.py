"""Tests for asset planning and platform rules."""

import unittest
from unittest.mock import patch

from app.data.platform_rules import PLATFORM_RULES, ASSET_TYPES, get_platform_rules
from app.graph.nodes.asset_planning import asset_planning


class AssetPlanningTests(unittest.TestCase):

    def test_all_platforms_have_rules(self):
        """All defined platforms must have image_rules."""
        for key, rules in PLATFORM_RULES.items():
            with self.subTest(platform=key):
                self.assertIn("image_rules", rules, f"{key} missing image_rules")
                self.assertIn("detail_page_rules", rules, f"{key} missing detail_page_rules")

    def test_asset_types_have_rules_per_platform(self):
        """Each asset type should have at least a max_count in each platform."""
        for key, rules in PLATFORM_RULES.items():
            image_rules = rules.get("image_rules", {})
            for at in ASSET_TYPES:
                if at == "7屏详情页":
                    continue  # Handled by detail_page_rules
                with self.subTest(platform=key, asset_type=at):
                    self.assertIn(at, image_rules,
                                  f"{key} missing rules for '{at}'")

    def test_platform_rules_differ_across_platforms(self):
        """Platforms should not have identical rules (smoke test for copy-paste)."""
        platforms = list(PLATFORM_RULES.keys())
        for i, p1 in enumerate(platforms):
            for p2 in platforms[i + 1:]:
                r1 = PLATFORM_RULES[p1].get("image_rules", {})
                r2 = PLATFORM_RULES[p2].get("image_rules", {})
                # At least one asset type should differ (by aspect_ratio OR rules)
                all_same = True
                for at in ASSET_TYPES:
                    if at == "7屏详情页":
                        continue
                    ar1 = r1.get(at, {}).get("aspect_ratio")
                    ar2 = r2.get(at, {}).get("aspect_ratio")
                    if ar1 and ar2 and ar1 != ar2:
                        all_same = False
                        break
                    # Also check rules list
                    rls1 = r1.get(at, {}).get("rules", [])
                    rls2 = r2.get(at, {}).get("rules", [])
                    if rls1 and rls2 and str(rls1) != str(rls2):
                        all_same = False
                        break
                self.assertFalse(all_same, f"{p1} and {p2} have identical rules!")

    def test_asset_planning_defaults_to_all_types(self):
        """When no asset_types_requested, generates plan for all ASSET_TYPES."""
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "tmall"},
            "product_name": "测试水杯",
            "asset_types_requested": [],
        })
        self.assertIn("asset_plan", result)
        self.assertIn("asset_prompts", result)
        # Should have plans for most types
        self.assertGreater(len(result["asset_plan"]), 0)

    def test_asset_planning_with_specific_types(self):
        """Only requested asset types appear in plan."""
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "amazon"},
            "product_name": "测试耳机",
            "asset_types_requested": [
                {"type_name": "主图", "count": 1},
                {"type_name": "使用场景图", "count": 2},
            ],
        })
        types_in_plan = [a["type"] for a in result["asset_plan"]]
        self.assertIn("主图", types_in_plan)
        self.assertIn("使用场景图", types_in_plan)
        self.assertNotIn("细节微距图", types_in_plan)

    def test_asset_planning_respects_platform_max_count(self):
        """Platform max_count should limit user-requested count."""
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "amazon"},
            "product_name": "测试",
            "asset_types_requested": [
                {"type_name": "主图", "count": 10},  # Amazon max is 1
            ],
        })
        main_item = [a for a in result["asset_plan"] if a["type"] == "主图"][0]
        self.assertEqual(main_item["count"], 1)  # Capped to platform max

    def test_asset_planning_image_roles(self):
        """image_roles from upload should be passed through."""
        state = {
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "tmall"},
            "product_name": "测试鞋",
            "asset_types_requested": [
                {"type_name": "主图", "count": 3},
            ],
            "images": ["img1.jpg", "img2.jpg", "img3.jpg"],
            "image_roles": ["front", "side", "back"],
        }
        result = asset_planning(state)
        main_item = [a for a in result["asset_plan"] if a["type"] == "主图"][0]
        self.assertIn("count", main_item)

    def test_asset_planning_seven_screen_compatibility(self):
        """7屏详情页 should generate prompts separately from per-type prompts."""
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "tmall"},
            "product_name": "测试",
            "asset_types_requested": [
                {"type_name": "主图", "count": 3},
                {"type_name": "7屏详情页", "count": 1},
            ],
        })
        asset_prompts = result["asset_prompts"]
        # asset_prompts should NOT contain 7屏详情页 (it uses existing prompts field)
        self.assertNotIn("7屏详情页", asset_prompts)
        # But it should be in the asset_plan
        detail_plan = [a for a in result["asset_plan"] if a["type"] == "7屏详情页"]
        self.assertEqual(len(detail_plan), 1)
        self.assertTrue(detail_plan[0].get("prompt_generated"))

    def test_get_platform_rules_function(self):
        """get_platform_rules returns correct platform."""
        amazon = get_platform_rules("amazon")
        self.assertIsNotNone(amazon)
        self.assertEqual(amazon["name"], "Amazon")

        tmall = get_platform_rules("tmall")
        self.assertIsNotNone(tmall)
        self.assertEqual(tmall["name"], "天猫")

        not_found = get_platform_rules("nonexistent")
        self.assertIsNone(not_found)

    # --- New dual-mode tests ---

    def test_smart_detail_skips_asset_plan(self):
        """smart_detail mode should return empty asset_plan and asset_prompts."""
        result = asset_planning({
            "generation_mode": "smart_detail",
            "user_constraints": {"platform": "tmall"},
            "product_name": "测试水杯",
            "asset_types_requested": [{"type_name": "主图", "count": 1}],
        })
        self.assertEqual(result["asset_plan"], [])
        self.assertEqual(result["asset_prompts"], {})
        self.assertEqual(result["platform_rules_applied"], {})

    def test_custom_assets_default_no_detail_produced_by_asset_planning(self):
        """custom_assets mode should still go through full asset planning (not skip)."""
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "tmall"},
            "product_name": "测试水杯",
            "asset_types_requested": [{"type_name": "主图", "count": 1}],
        })
        # Asset planning should still produce plan/prompts for custom_assets mode
        self.assertGreater(len(result["asset_plan"]), 0)
        self.assertIn("主图", result["asset_prompts"])

    def test_hybrid_generates_asset_plan(self):
        """hybrid mode should still go through full asset planning."""
        result = asset_planning({
            "generation_mode": "hybrid",
            "user_constraints": {"platform": "tmall"},
            "product_name": "测试水杯",
            "asset_types_requested": [{"type_name": "主图", "count": 1}],
        })
        self.assertGreater(len(result["asset_plan"]), 0)
        self.assertIn("主图", result["asset_prompts"])

    def test_screen_product_main_image_prompt_requires_lit_generic_ui(self):
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "amazon"},
            "product_name": "测血压手表",
            "product_type": "电子产品",
            "output_language": "English",
            "user_selling_points": ["运动记录", "消息提醒"],
            "asset_types_requested": [{"type_name": "主图", "count": 1}],
        })

        prompt = result["asset_prompts"]["主图"][0]

        self.assertIn("屏幕必须点亮", prompt)
        self.assertIn("通用非品牌化", prompt)
        self.assertIn("画面文字语言：English", prompt)
        self.assertIn("屏幕 UI 上的所有可见文字必须使用 English", prompt)
        self.assertIn("Amazon 合规白底", prompt)
        self.assertIn("避免死板黑屏", prompt)
        self.assertIn("不得出现 Apple", prompt)

    def test_non_screen_product_prompt_is_not_forced_to_lit_ui(self):
        result = asset_planning({
            "generation_mode": "custom_assets",
            "user_constraints": {"platform": "amazon"},
            "product_name": "陶瓷马克杯",
            "product_type": "家居百货",
            "asset_types_requested": [{"type_name": "主图", "count": 1}],
        })

        prompt = result["asset_prompts"]["主图"][0]

        self.assertNotIn("屏幕必须点亮", prompt)
        self.assertNotIn("通用非品牌化", prompt)


if __name__ == "__main__":
    unittest.main()
