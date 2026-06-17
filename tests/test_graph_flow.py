import unittest
from unittest.mock import patch

from app.graph.builder import build_graph
from app.graph.nodes.completion import ai_completion
from app.graph.nodes.image_generation import image_generation
from app.graph.nodes.prompt_generator import prompt_generator
from app.graph.nodes.prompt_revision import prompt_revision
from app.graph.nodes.qa import qa_inspector, should_revise
from app.graph.nodes.vision import vision_product_parser
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT
from app.schemas.requests import GenerateRequest
from app.services.llm import LLMServiceError


class GraphFlowTests(unittest.TestCase):

    def setUp(self):
        self._mock_live = patch("app.services.llm.should_use_live_llm", return_value=False)
        self._mock_live.start()

    def tearDown(self):
        self._mock_live.stop()

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
        self.assertEqual(state["output_language"], "中文")
        self.assertEqual(state["user_specs"]["output_language"], "中文")

    def test_generate_request_infers_and_overrides_output_language(self):
        default_state = GenerateRequest(target_market="拉美").to_state()
        override_state = GenerateRequest(target_market="美国", output_language="Spanish").to_state()

        self.assertEqual(default_state["output_language"], "Spanish")
        self.assertEqual(default_state["user_specs"]["output_language"], "Spanish")
        self.assertEqual(override_state["output_language"], "Spanish")
        self.assertEqual(override_state["user_specs"]["output_language"], "Spanish")

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
                "output_language": "English",
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
        self.assertEqual(result["output_language"], "English")
        self.assertIn("画面文字语言：English", first_prompt)
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

    def test_image_generation_live_dispatches_with_limit(self):
        state = {
            "user_constraints": {"enable_image_generation": True},
            "detail_prompts": {"screen_1": "detail prompt"},
            "asset_prompts": {"主图": ["asset prompt 1", "asset prompt 2"]},
            "errors": [],
        }

        fake_image = {
            "id": "asset:主图:1",
            "type": "asset",
            "model": "gpt-image-2",
            "size": "1024x1024",
            "quality": "high",
            "prompt": "asset prompt 1",
            "b64_json": "abc",
            "url": None,
            "revised_prompt": None,
            "error": None,
        }
        with patch("app.services.llm.should_use_live_llm", return_value=True), patch(
            "app.services.llm.generate_image",
            return_value=fake_image,
        ) as generate_image, patch("app.graph.nodes.image_generation.settings.max_images_per_request", 1):
            result = image_generation(state)

        # limited by MAX_IMAGES_PER_REQUEST=1
        self.assertLessEqual(len(result["generated_images"]), 1)
        # limited by MAX_IMAGES_PER_REQUEST=1
        self.assertEqual(generate_image.call_count, 1)
        self.assertTrue(result["image_generation_status"]["enabled"])
        self.assertEqual(result["image_generation_status"]["mode"], "live")

    def test_image_generation_enabled_without_live_returns_placeholders(self):
        result = image_generation(
            {
                "user_constraints": {"enable_image_generation": True},
                "detail_prompts": {},
                "asset_prompts": {"主图": ["asset prompt"]},
            }
        )

        self.assertEqual(result["image_generation_status"]["mode"], "mock_fallback")
        self.assertEqual(result["image_generation_status"]["generated_count"], 0)
        self.assertIn("asset:主图:1", result["generated_images"])
        self.assertIsNotNone(result["generated_images"]["asset:主图:1"]["error"])

    def test_completion_live_failure_falls_back_to_mock(self):
        state = {
            "merged_data": {"product_type": {"value": "保温杯"}},
            "missing_fields": ["brand", "selling_points"],
            "errors": [],
        }

        with patch("app.services.llm.should_use_live_llm", return_value=True), patch(
            "app.services.llm.complete_product_data",
            side_effect=LLMServiceError("temporary live failure"),
        ):
            result = ai_completion(state)

        self.assertEqual(result["llm_mode_used"], "mock_fallback")
        self.assertEqual(result["completed_data"]["brand"]["value"], "未识别品牌")
        self.assertEqual(result["errors"][0]["node"], "completion")

    def test_vision_live_dispatches_service_result(self):
        live_vision = {
            "raw_ocr": ["TEST"],
            "visual_elements": [{"value": "正面包装", "confidence": 0.9, "source": "vision"}],
            "packaging": {"brand": {"value": "LiveBrand", "confidence": 0.9, "source": "vision"}},
            "text_detected": ["TEST"],
            "materials_guess": [],
            "design_features": [],
            "selling_signals": [],
            "user_guess": {},
            "confidence": {"overall": 0.9},
        }

        with patch("app.services.llm.should_use_live_llm", return_value=True), patch(
            "app.services.llm.parse_product_images",
            return_value=live_vision,
        ):
            result = vision_product_parser({"images": ["data:image/png;base64,abc"], "errors": []})

        self.assertEqual(result["vision_mode_used"], "live")
        self.assertEqual(result["vision_data"]["packaging"]["brand"]["value"], "LiveBrand")

    def test_vision_live_failure_falls_back_to_mock(self):
        with patch("app.services.llm.should_use_live_llm", return_value=True), patch(
            "app.services.llm.parse_product_images",
            side_effect=LLMServiceError("vision failure"),
        ):
            result = vision_product_parser(
                {
                    "images": ["data:image/png;base64,abc"],
                    "user_specs": {"brand": "FallbackBrand", "product_type": "水杯"},
                    "errors": [],
                }
            )

        self.assertEqual(result["vision_mode_used"], "mock_fallback")
        self.assertEqual(result["vision_data"]["packaging"]["brand"]["value"], "FallbackBrand")
        self.assertEqual(result["errors"][0]["node"], "vision")

    def test_vision_live_without_images_uses_mock_without_calling_service(self):
        with patch("app.services.llm.should_use_live_llm", return_value=True), patch(
            "app.services.llm.parse_product_images",
        ) as parse_images:
            result = vision_product_parser({"images": [], "errors": []})

        parse_images.assert_not_called()
        self.assertNotIn("vision_mode_used", result)
        self.assertEqual(result["vision_data"]["confidence"]["overall"], 0.1)

    def test_prompt_generator_live_dispatches_service_result(self):
        live_result = {
            "detail_prompts": {f"screen_{i}": f"主标题：Live {i}\n副标题：测试" for i in range(1, 8)},
            "prompts": {f"screen_{i}": f"主标题：Live {i}\n副标题：测试" for i in range(1, 8)},
            "asset_prompts": {},
        }

        with patch("app.services.llm.should_use_live_llm", return_value=True), patch(
            "app.services.llm.generate_prompts",
            return_value=live_result,
        ):
            result = prompt_generator({"generation_mode": "smart_detail"})

        self.assertEqual(result["llm_mode_used"], "live")
        self.assertEqual(result["detail_prompts"]["screen_1"], "主标题：Live 1\n副标题：测试")

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
