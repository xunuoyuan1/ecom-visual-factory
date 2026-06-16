import unittest

from app.graph.builder import build_graph
from app.graph.nodes.prompt_revision import prompt_revision
from app.graph.nodes.qa import qa_inspector, should_revise
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT
from app.schemas.requests import GenerateRequest


class GraphFlowTests(unittest.TestCase):
    def test_generate_request_merges_top_level_product_fields_into_specs(self):
        request = GenerateRequest(
            product_name="保温杯",
            brand="Test",
            product_type="家居",
            target_audience="办公室人群",
            selling_points=["保温", "便携", "防漏"],
        )

        state = request.to_state()

        self.assertEqual(state["user_specs"]["brand"], "Test")
        self.assertEqual(state["user_specs"]["product_type"], "家居")
        self.assertEqual(state["user_specs"]["target_audience"], "办公室人群")
        self.assertEqual(state["user_specs"]["product_name"], "保温杯")

    def test_incomplete_input_uses_completion_and_generates_seven_prompts(self):
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-1",
                "sku_id": "sku-1",
                "images": ["image-a"],
                "user_specs": {"product_type": "护手霜"},
                "user_selling_points": ["滋润"],
                "user_constraints": {"enable_web_enhancement": True, "max_qa_iterations": 1},
                "generation_mode": "smart_detail",
                "include_detail_screens": False,
                "iteration": 0,
                "errors": [],
            }
        )

        self.assertEqual(result["route"], "completion")
        self.assertIn("completed_data", result)
        self.assertEqual(len(result["detail_prompts"]), 7)
        self.assertTrue(result["qa_report"]["pass"])
        for prompt in result["detail_prompts"].values():
            self.assertIn("主标题：", prompt)
            self.assertIn("副标题：", prompt)

    def test_complete_input_skips_completion(self):
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-2",
                "sku_id": "sku-2",
                "images": ["a", "b", "c"],
                "user_specs": {
                    "brand": "测试品牌",
                    "product_type": "咖啡杯",
                    "target_audience": "办公室人群",
                },
                "user_selling_points": ["陶瓷质感", "易清洁", "适合办公桌"],
                "user_constraints": {"enable_web_enhancement": False, "max_qa_iterations": 1},
                "generation_mode": "smart_detail",
                "include_detail_screens": False,
                "iteration": 0,
                "errors": [],
            }
        )

        self.assertEqual(result["route"], "direct")
        self.assertNotIn("completed_data", result)
        self.assertEqual(len(result["prompts"]), 7)
        self.assertIn("Web enhancement disabled", result["market_data"]["industry_source_note"])

    def test_qa_revision_adds_missing_fidelity_requirement(self):
        state = {
            "prompts": {f"screen_{i}": "主标题：测试\n副标题：测试\n画面比例为2:3竖版" for i in range(1, 8)},
            "user_constraints": {"max_qa_iterations": 1},
            "iteration": 0,
        }

        state.update(qa_inspector(state))
        self.assertEqual(should_revise(state), "revise")
        self.assertFalse(state["qa_report"]["pass"])

        state.update(prompt_revision(state))
        state.update(qa_inspector(state))

        self.assertEqual(state["iteration"], 1)
        self.assertTrue(state["qa_report"]["pass"])
        for prompt in state["prompts"].values():
            self.assertIn(PRODUCT_FIDELITY_REQUIREMENT, prompt)

    def test_smart_detail_has_empty_asset_plan(self):
        """In smart_detail mode, asset planning returns empty, but detail_prompts filled."""
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-3",
                "sku_id": "sku-3",
                "images": ["img1"],
                "user_specs": {"product_type": "护手霜"},
                "user_selling_points": ["滋润"],
                "user_constraints": {"platform": "tmall", "enable_web_enhancement": True, "max_qa_iterations": 1},
                "generation_mode": "smart_detail",
                "include_detail_screens": False,
                "iteration": 0,
                "errors": [],
            }
        )
        # Smart_detail: asset plan empty, but detail_prompts populated
        self.assertEqual(result.get("asset_plan"), [])
        self.assertIn("detail_prompts", result)
        self.assertEqual(len(result["detail_prompts"]), 7)

    def test_top_level_product_fields_feed_detail_prompts(self):
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-top-level-fields",
                "sku_id": "sku-top-level-fields",
                "product_name": "保温杯",
                "brand": "Test",
                "product_type": "家居",
                "target_audience": "办公室人群",
                "images": [],
                "image_roles": [],
                "user_specs": {
                    "brand": "Test",
                    "product_type": "家居",
                    "target_audience": "办公室人群",
                    "product_name": "保温杯",
                },
                "user_selling_points": ["保温", "便携", "防漏"],
                "user_constraints": {
                    "generation_mode": "smart_detail",
                    "text_only_mode": True,
                    "max_qa_iterations": 1,
                },
                "generation_mode": "smart_detail",
                "include_detail_screens": False,
                "iteration": 0,
                "errors": [],
            }
        )

        first_prompt = next(iter(result["detail_prompts"].values()))
        self.assertEqual(result["cleaned_data"]["brand"]["value"], "Test")
        self.assertEqual(result["cleaned_data"]["product_type"]["value"], "家居")
        self.assertIn("主标题：Test家居", first_prompt)
        self.assertNotIn("未识别品牌电商商品", first_prompt)

    def test_custom_assets_no_detail_skips_prompts(self):
        """custom_assets without include_detail_screens should not generate prompts or detail_prompts."""
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-4",
                "sku_id": "sku-4",
                "images": ["img1"],
                "user_specs": {"product_type": "护手霜", "brand": "TestBrand"},
                "user_selling_points": ["滋润"],
                "user_constraints": {"platform": "tmall", "enable_web_enhancement": True, "max_qa_iterations": 1},
                "generation_mode": "custom_assets",
                "include_detail_screens": False,
                "asset_types_requested": [{"type_name": "主图", "count": 1}],
                "iteration": 0,
                "errors": [],
            }
        )
        # Should have asset_plan but NOT prompts or detail_prompts
        self.assertGreater(len(result.get("asset_plan", [])), 0)
        self.assertEqual(result.get("prompts", None), {})
        self.assertEqual(result.get("detail_prompts", None), {})

    def test_custom_assets_image_generation_uses_asset_prompts(self):
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-custom-image",
                "sku_id": "sku-custom-image",
                "product_name": "保温杯",
                "images": [],
                "image_roles": [],
                "user_specs": {"brand": "Test", "product_type": "家居"},
                "user_selling_points": ["保温", "便携", "防漏"],
                "asset_types_requested": [{"type_name": "主图", "count": 1}],
                "user_constraints": {
                    "platform": "amazon",
                    "generation_mode": "custom_assets",
                    "include_detail_screens": False,
                    "enable_image_generation": True,
                    "text_only_mode": True,
                    "max_qa_iterations": 1,
                },
                "generation_mode": "custom_assets",
                "include_detail_screens": False,
                "iteration": 0,
                "errors": [],
            }
        )

        self.assertEqual(result["detail_prompts"], {})
        self.assertEqual(result["prompts"], {})
        self.assertIn("asset:主图:1", result["generated_images"])

    def test_custom_assets_with_detail_screens_generates_both(self):
        """custom_assets + include_detail_screens=True should generate both asset_prompts and detail_prompts."""
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-5",
                "sku_id": "sku-5",
                "images": ["img1"],
                "user_specs": {"product_type": "护手霜", "brand": "TestBrand"},
                "user_selling_points": ["滋润"],
                "user_constraints": {"platform": "tmall", "enable_web_enhancement": True, "max_qa_iterations": 1},
                "generation_mode": "custom_assets",
                "include_detail_screens": True,
                "asset_types_requested": [{"type_name": "主图", "count": 1}],
                "iteration": 0,
                "errors": [],
            }
        )
        self.assertGreater(len(result.get("asset_plan", [])), 0)
        self.assertEqual(len(result.get("detail_prompts", {})), 7)
        self.assertEqual(len(result.get("prompts", {})), 7)

    def test_hybrid_generates_both(self):
        """hybrid mode should produce both detail_prompts and asset_prompts."""
        graph = build_graph()
        result = graph.invoke(
            {
                "job_id": "job-6",
                "sku_id": "sku-6",
                "images": ["img1"],
                "user_specs": {"product_type": "护手霜", "brand": "TestBrand"},
                "user_selling_points": ["滋润"],
                "user_constraints": {"platform": "tmall", "enable_web_enhancement": True, "max_qa_iterations": 1},
                "generation_mode": "hybrid",
                "include_detail_screens": False,
                "asset_types_requested": [{"type_name": "主图", "count": 2}],
                "iteration": 0,
                "errors": [],
            }
        )
        # Hybrid: both detail and asset prompts populated
        self.assertEqual(len(result.get("detail_prompts", {})), 7)
        self.assertEqual(len(result.get("prompts", {})), 7)
        self.assertIn("asset_prompts", result)
        self.assertIn("主图", result.get("asset_prompts", {}))


if __name__ == "__main__":
    unittest.main()
