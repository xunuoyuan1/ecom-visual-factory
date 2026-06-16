import unittest

from app.graph.builder import build_graph
from app.graph.nodes.prompt_revision import prompt_revision
from app.graph.nodes.qa import qa_inspector, should_revise
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT


class GraphFlowTests(unittest.TestCase):
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
                "iteration": 0,
                "errors": [],
            }
        )

        self.assertEqual(result["route"], "completion")
        self.assertIn("completed_data", result)
        self.assertEqual(len(result["prompts"]), 7)
        self.assertTrue(result["qa_report"]["pass"])
        for prompt in result["prompts"].values():
            self.assertIn("主标题：", prompt)
            self.assertIn("副标题：", prompt)
            self.assertIn(PRODUCT_FIDELITY_REQUIREMENT, prompt)

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


if __name__ == "__main__":
    unittest.main()
