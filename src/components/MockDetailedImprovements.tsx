'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MockDetailedImprovementsProps {
  essayContent: string;
  essayTitle: string;
  dimensionScores: Record<string, number>;
  overallScore: number;
}

// 模拟的详细改进建议数据
const MOCK_IMPROVEMENTS = {
  comprehensive: `# 📋 综合详细改进建议

## 总体评价
你这篇文章的立场非常清晰，并且尝试用不同的论点来支撑你的观点，也做到了分段，这是一个很好的起点。

但是，文章在**论证的展开、语言的准确性和多样性、以及句子的连接方面有很大的提升空间**。按照雅思官方评分标准，这篇文章目前的水平大约在 **5.0分** 左右。主要问题在于语法错误较多，影响了意思的清晰表达，同时词汇和句式比较单一和重复。

## 分项解析与修改建议

### 1. 任务回应 (Task Response - TR)
你的文章明确地表达了同意"公司和个人应该为治污买单"的观点，并贯穿全文，这一点是符合要求的。但主要问题在于论点的展开和论证不够充分和清晰。

**优点:**
- 立场明确 (clear position)

**问题与修改建议:**

#### 论点过于笼统，缺乏深度:
**原文:** "...it will produce a result that is bring the best gdp for the society which is proved by the economics."

**分析:** 这个"被经济学证明"的说法太空泛了。读者不明白为什么让企业和个人付钱就能带来最好的GDP。你需要解释背后的逻辑，比如这会促进环保技术产业的发展，或者促使企业将治污成本内部化，从而进行更高效的资源配置。

**建议:** 展开论述，可以引入"污染者付费原则 (the polluter pays principle)"这个概念，说明这是一种将环境成本纳入生产成本的公平且高效的经济手段。

#### 例子不具说服力:
**原文:** "...the governmen which pay to clean the pollution shut the company down because of lacking money to pay for it."

**分析:** 这个例子不太合乎逻辑。政府通常不会因为没钱治理污染而直接关停一个盈利的公司。这个例子削弱了你的论证力量。

**建议:** 可以换一个更有力的例子。比如，如果政府买单，企业就没有动力去减少污染，它们会继续污染，而治理的费用最终会通过税收转嫁给所有纳税人，这对不制造污染的公民是不公平的，也无法从源头上遏制污染。

### 2. 连贯与衔接 (Coherence and Cohesion - CC)
文章有分段，结构意识是有的。但句子之间的连接过于简单，逻辑推进不够流畅。

**优点:**
- 文章有基本的结构：引言、主体段落、结论

**问题与修改建议:**

#### 过度使用 "And":
你多次用 "And" 来开始一个句子，这让文章显得单调且口语化。

**建议:** 使用更多样的连接词来展示逻辑关系。例如：
- 表示递进: Moreover, Furthermore, In addition
- 表示因果: Therefore, As a result, Consequently  
- 表示转折: However, Nevertheless

#### 修改示范:
**原文:** "Because if nobody pay to clean the pollution, the environment will be damaged... And if the government pay to clean the pollution, it couldn't protect the environment to best."

**修改后:** "This approach is crucial because relying on no one would lead to irreversible environmental damage. Alternatively, if the responsibility falls solely on the government, the outcome is also suboptimal." (使用 Alternatively 来连接两种不同的情况，逻辑更清晰。)

### 3. 词汇丰富度 (Lexical Resource - LR)
你的词汇量比较基础，且存在一些拼写和用词不当的错误，这影响了表达的准确性。

**问题与修改建议:**

#### 用词重复:
"pay to clean pollution", "companies and individuals", "environment", "pollution" 等词反复出现。

**建议替换:**
- companies and individuals: corporations and citizens, private entities, polluters
- pay for: finance, fund, bear the cost of, take financial responsibility for
- clean pollution: pollution cleanup, environmental remediation, mitigating pollution
- pollution: environmental degradation, contamination, harmful emissions

#### 拼写错误:
- effiecient → efficient
- maxmize → maximize
- environement → environment
- extend → extent
- governmen → government
- companis → companies

#### 用词不当:
- human will extinct → humanity will become extinct (extinct是形容词)
- to the best extend → to the greatest extent
- bring the best gdp → contribute most effectively to the GDP

### 4. 语法多样性及准确性 (Grammatical Range and Accuracy - GRA)
这是你目前最需要提高的部分。文章中存在大量语法错误，包括句子结构、动词时态、主谓一致等，严重影响了读者理解。

**问题与修改建议:**

#### 句子结构混乱:
**原文:** "Some people think companies and individuals should pay to clean pollution.And I think the opinion is right especially when companies and individuals pay to what cost to the society."

**分析:** "And" 前面应该是句号，后面大写。后半句 "pay to what cost to the society" 结构和意思都不清晰。

**修改后:** "Some people argue that companies and individuals, rather than governments, should be financially responsible for cleaning up pollution. In my view, this opinion is largely correct, as it aligns with fundamental principles of accountability."

#### 主谓不一致:
**原文:** "The profits is gained..."
**修改后:** "The profits are gained..."

#### 动词形式错误:
**原文:** "...a result that is bring the best gdp..."
**修改后:** "...a result that brings the best gdp..." or "...a result that would bring..."

## 优化范文示例

基于你的思路，这里是一个优化版本：

**Topic:** The companies and individuals (not governments) should pay to clean pollution. To what extent do you agree or disagree?

It is often argued that the financial burden of environmental remediation should fall on corporations and individuals, not on the state. I wholeheartedly agree with this proposition, as it is not only a more efficient economic model but also a more equitable approach to environmental protection.

The primary argument in favour of this policy is its economic efficiency, a concept often referred to as the "polluter pays principle." When businesses are required to fund the cleanup of the pollution they generate, these environmental costs are internalized into their operational expenses. This financial incentive compels them to innovate and adopt cleaner technologies to minimize pollution from the outset, rather than treating the environment as a free resource to exploit.

Furthermore, making polluters pay is fundamental to effective environmental preservation. If governments assume the full responsibility for cleanup, funded by general taxation, a moral hazard is created. Companies might lack the motivation to reduce their harmful emissions, knowing that the public will ultimately foot the bill.

Finally, this approach is rooted in the principle of fairness and social responsibility. Corporations that profit from industrial activities have a corresponding duty to mitigate the negative impacts of their operations. It would be profoundly unfair for the general public, including those who make conscious efforts to live sustainably, to subsidize the cleanup costs for profit-making enterprises.

In conclusion, for reasons of economic prudence, environmental effectiveness, and social fairness, I am firmly convinced that companies and individuals should be held financially liable for the pollution they create.

## 下一步改进建议

1. **立即行动:**
   - 仔细检查每个句子的语法结构
   - 使用语法检查工具辅助修改
   - 练习使用更多样的连接词

2. **学习重点:**
   - 掌握复合句和复杂句的构造
   - 学习学术写作的词汇和表达
   - 练习段落内部的逻辑连接

3. **练习建议:**
   - 每天写一个段落，重点练习语法准确性
   - 阅读高分范文，学习句式结构
   - 做语法专项练习，特别是主谓一致和动词时态`,

  sentence: `# 📝 逐句详细分析

## 句子1: "Some people think companies and individuals should pay to clean pollution."

### 语法分析
- **结构:** 主语 + 谓语 + 宾语从句
- **时态:** 一般现在时，正确
- **主谓一致:** 正确

### 词汇分析
- **基础词汇过多:** "think", "pay", "clean" 都是基础词汇
- **建议升级:**
  - think → argue, believe, contend, maintain
  - pay → bear the financial responsibility for, fund
  - clean pollution → environmental remediation, pollution cleanup

### 改进版本
**版本1 (中级):** "Some people argue that companies and individuals should bear the financial responsibility for pollution cleanup."

**版本2 (高级):** "It is contended by some that corporations and private citizens, rather than governments, should assume financial liability for environmental remediation."

**版本3 (学术):** "There is a prevailing argument that the financial burden of pollution mitigation should rest with private entities rather than public institutions."

---

## 句子2: "And I think the opinion is right especially when companies and individuals pay to what cost to the society."

### 语法分析
- **严重错误:** "pay to what cost to the society" 结构完全错误
- **连接词问题:** 用"And"开头过于口语化
- **语法结构混乱:** 整个句子意思不清

### 词汇分析
- **重复使用:** "think" 在前一句刚用过
- **表达不准确:** "what cost to the society" 意思不明

### 改进版本
**版本1 (基础修正):** "I believe this opinion is correct, especially when considering the social costs that companies and individuals should bear."

**版本2 (中级):** "In my view, this perspective is justified, particularly when we consider that polluting entities should internalize the social costs of their actions."

**版本3 (高级):** "I wholeheartedly endorse this viewpoint, as it reflects the fundamental principle that those who generate negative externalities should bear the associated social costs."

---

## 句子3: "Because if nobody pay to clean the pollution, the environment will be damaged and human will extinct."

### 语法分析
- **主谓不一致:** "nobody pay" → "nobody pays"
- **词性错误:** "human will extinct" → "humanity will become extinct"
- **句子结构:** 条件句结构基本正确，但表达过于绝对

### 词汇分析
- **用词不当:** "extinct" 是形容词，不能作动词
- **表达过于极端:** "human will extinct" 过于绝对化

### 改进版本
**版本1 (语法修正):** "Because if nobody pays to clean the pollution, the environment will be damaged and humanity could face extinction."

**版本2 (逻辑改进):** "Without proper funding for pollution cleanup, environmental degradation would accelerate, potentially threatening human survival."

**版本3 (学术表达):** "In the absence of adequate financial mechanisms for environmental remediation, ecological systems would deteriorate, posing existential risks to human civilization."

---

## 句子4: "And if the government pay to clean the pollution, it couldn't protect the environment to best."

### 语法分析
- **主谓不一致:** "government pay" → "government pays"
- **表达不当:** "to best" → "to the best extent" 或 "optimally"
- **逻辑不清:** 为什么政府付费就不能最好地保护环境？

### 词汇分析
- **表达不完整:** "to best" 不是完整表达
- **逻辑跳跃:** 缺少解释政府付费为什么效果不好

### 改进版本
**版本1 (基础修正):** "And if the government pays to clean the pollution, it couldn't protect the environment optimally."

**版本2 (逻辑完善):** "However, if the government bears this cost, it may not achieve optimal environmental protection due to budget constraints and lack of direct incentives for polluters to reduce emissions."

**版本3 (深度分析):** "Conversely, government-funded cleanup programs may prove suboptimal, as they fail to create direct financial incentives for polluting entities to modify their behavior, potentially perpetuating a cycle of environmental damage."

---

## 整体句式改进建议

### 1. 避免简单句堆砌
**当前问题:** 大多数句子都是简单的主谓宾结构
**改进方向:** 使用复合句、复杂句增加句式多样性

### 2. 改善句子连接
**当前问题:** 过度依赖"And"连接
**改进方向:** 使用多样化的连接词和过渡短语

### 3. 提升词汇层次
**当前问题:** 基础词汇重复使用
**改进方向:** 使用同义词替换，提升学术词汇比例

### 4. 加强逻辑表达
**当前问题:** 论证跳跃，缺少解释
**改进方向:** 增加因果关系的明确表达`,

  error: `# 🔍 全面错误分析

## 错误统计概览
- **语法错误:** 20处
- **词汇错误:** 7处  
- **结构错误:** 12处
- **标点错误:** 12处
- **学术写作规范错误:** 8处

---

## 1. 语法错误详细分析

### 主谓一致错误 (Subject-Verb Agreement)

#### 错误1: "nobody pay"
**位置:** 第3句
**错误类型:** 主谓不一致
**原文:** "Because if nobody pay to clean the pollution..."
**修正:** "Because if nobody pays to clean the pollution..."
**解释:** "nobody" 是单数主语，动词应该用第三人称单数形式 "pays"

#### 错误2: "government pay"  
**位置:** 第4句
**错误类型:** 主谓不一致
**原文:** "And if the government pay to clean the pollution..."
**修正:** "And if the government pays to clean the pollution..."
**解释:** "government" 是单数名词，动词应该用 "pays"

#### 错误3: "The profits is gained"
**位置:** 第6句
**错误类型:** 主谓不一致
**原文:** "The profits is gained by the company..."
**修正:** "The profits are gained by the company..."
**解释:** "profits" 是复数名词，应该用 "are"

### 动词形式错误 (Verb Form Errors)

#### 错误4: "that is bring"
**位置:** 第5句
**错误类型:** 动词形式错误
**原文:** "...a result that is bring the best gdp..."
**修正:** "...a result that brings the best gdp..." 或 "...a result that would bring..."
**解释:** 定语从句中应该用动词原形 "brings" 或情态动词结构

#### 错误5: "human will extinct"
**位置:** 第3句
**错误类型:** 词性误用
**原文:** "...and human will extinct."
**修正:** "...and humanity will become extinct." 或 "...and humans will face extinction."
**解释:** "extinct" 是形容词，不能直接作动词使用

### 介词错误 (Preposition Errors)

#### 错误6: "pay to clean"
**位置:** 多处
**错误类型:** 介词使用不当
**原文:** "pay to clean pollution"
**修正:** "pay for cleaning pollution" 或 "pay to clean up pollution"
**解释:** "pay for" 更适合表示为某事付费

#### 错误7: "to the best extend"
**位置:** 第6句
**错误类型:** 介词搭配错误
**原文:** "...to the best extend"
**修正:** "...to the greatest extent"
**解释:** 正确搭配是 "to the greatest extent"

---

## 2. 词汇错误详细分析

### 拼写错误 (Spelling Errors)

#### 错误8: "effiecient"
**位置:** 第6句
**正确拼写:** efficient
**记忆技巧:** ef-fi-cient，注意中间是 "fi" 不是 "fie"

#### 错误9: "maxmize"
**位置:** 第6句  
**正确拼写:** maximize
**记忆技巧:** maxim-ize，来自 "maximum"

#### 错误10: "environement"
**位置:** 第6句
**正确拼写:** environment
**记忆技巧:** environ-ment，注意中间没有额外的 "e"

#### 错误11: "governmen"
**位置:** 第5句
**正确拼写:** government
**记忆技巧:** govern-ment，注意结尾是完整的 "ment"

#### 错误12: "companis"
**位置:** 第7句
**正确拼写:** companies
**记忆技巧:** company 的复数形式，y 变 ies

### 词汇选择错误 (Word Choice Errors)

#### 错误13: "extend" vs "extent"
**位置:** 第6句
**错误用法:** "to the best extend"
**正确用法:** "to the greatest extent"
**区别:** extend 是动词（延伸），extent 是名词（程度）

#### 错误14: "bring the best gdp"
**位置:** 第5句
**问题:** 表达不地道
**改进:** "contribute most effectively to GDP growth" 或 "optimize economic output"

---

## 3. 句子结构错误

### 句子片段 (Sentence Fragments)

#### 错误15: 不完整的表达
**原文:** "pay to what cost to the society"
**问题:** 句子结构混乱，意思不清
**修正:** "bear the social costs" 或 "internalize the social costs of their actions"

### 流水句 (Run-on Sentences)

#### 错误16: 过长复杂句
**原文:** "Besides rights should always equals to responsibilities if the companis that produce extensive pollution are treated like other companies is also unfair."
**问题:** 一个句子包含多个主语和谓语，结构混乱
**修正:** 分解为两个句子：
"Furthermore, rights should always be balanced with responsibilities. It would be unfair if companies that produce extensive pollution were treated the same as environmentally responsible businesses."

---

## 4. 标点符号错误

### 句号和连接词

#### 错误17: "pollution.And"
**问题:** 句号后直接跟连接词，应该分开或用逗号
**修正:** "pollution. And" 或 "pollution, and"

### 逗号使用

#### 错误18: 缺少必要逗号
**原文:** "Besides rights should always equals to responsibilities..."
**修正:** "Besides, rights should always equal responsibilities..."
**解释:** 介词短语开头需要逗号分隔

---

## 5. 学术写作规范错误

### 非正式表达

#### 错误19: 过度使用 "And" 开头
**问题:** "And I think...", "And if the government..."
**改进:** 使用更正式的连接词如 "Furthermore", "Moreover", "Additionally"

#### 错误20: 口语化表达
**原文:** "I think the opinion is right"
**改进:** "In my view, this perspective is justified" 或 "I believe this argument is valid"

---

## 修正建议优先级

### 🔴 高优先级（立即修正）
1. 主谓一致错误
2. 基本拼写错误
3. 句子结构混乱

### 🟡 中优先级（重点改进）
1. 动词形式和时态
2. 介词搭配
3. 词汇选择准确性

### 🟢 低优先级（长期提升）
1. 学术写作风格
2. 句式多样性
3. 高级词汇使用

## 系统性改进计划

### 第1周：语法基础
- 每天练习主谓一致
- 复习基本动词时态
- 使用语法检查工具

### 第2周：词汇提升  
- 建立错误词汇本
- 每天学习5个学术词汇
- 练习同义词替换

### 第3周：句式结构
- 学习复合句构造
- 练习使用连接词
- 避免句子片段和流水句

### 第4周：综合应用
- 重写原文，应用所学
- 请他人检查语法错误
- 对比修改前后的差异`
};

export default function MockDetailedImprovements({
  essayContent,
  essayTitle,
  dimensionScores,
  overallScore
}: MockDetailedImprovementsProps) {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sections = [
    { key: 'comprehensive', title: '📋 综合详细改进建议', description: '基于所有数据资源的深度分析' },
    { key: 'sentence', title: '📝 逐句详细分析', description: '对每个句子进行深度分析和改进' },
    { key: 'error', title: '🔍 全面错误分析', description: '识别和修正所有类型的错误' }
  ];

  const generateImprovement = async (sectionKey: string) => {
    setIsLoading(true);
    setActiveSection(sectionKey);
    
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setIsLoading(false);
  };

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      alert('内容已复制到剪贴板！');
    } catch (error) {
      console.error('复制失败:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">🎯 详细改进建议 (演示版)</h3>
        <p className="text-gray-600 text-sm">
          这是详细改进建议功能的演示版本。点击下方按钮查看AI生成的详细改进建议示例。
          实际使用时，AI会根据您的具体作文内容生成个性化的建议。
        </p>
      </div>

      <div className="space-y-4">
        {sections.map((section) => (
          <div key={section.key} className="border border-gray-200 rounded-lg">
            {/* Section Header */}
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900">{section.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{section.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {activeSection === section.key && !isLoading && (
                    <>
                      <button
                        onClick={() => copyToClipboard(MOCK_IMPROVEMENTS[section.key as keyof typeof MOCK_IMPROVEMENTS])}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                        title="复制内容"
                      >
                        📋
                      </button>
                      <button
                        onClick={() => setActiveSection(activeSection === section.key ? null : section.key)}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                        title={activeSection === section.key ? "折叠" : "展开"}
                      >
                        {activeSection === section.key ? '🔼' : '🔽'}
                      </button>
                    </>
                  )}
                  {activeSection !== section.key && !isLoading && (
                    <button
                      onClick={() => generateImprovement(section.key)}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                    >
                      生成建议
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Loading State */}
            {isLoading && activeSection === section.key && (
              <div className="p-6">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                  <span className="text-gray-600">AI正在生成详细的改进建议，请稍候...</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div className="bg-indigo-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-blue-800 text-sm">
                    💡 AI正在深度分析您的作文，生成的建议将非常详细和具体，请耐心等待...
                  </p>
                </div>
              </div>
            )}

            {/* Content */}
            {activeSection === section.key && !isLoading && (
              <div className="p-6">
                <div className="prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {MOCK_IMPROVEMENTS[section.key as keyof typeof MOCK_IMPROVEMENTS]}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 使用说明 */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h5 className="font-semibold text-yellow-800 mb-2">📚 功能说明</h5>
        <ul className="text-yellow-700 text-sm space-y-1">
          <li>• <strong>综合详细改进建议</strong>：最全面的分析，包含四个维度的详细评价和具体改进建议</li>
          <li>• <strong>逐句详细分析</strong>：对每个句子进行语法、词汇、结构分析，提供多个改进版本</li>
          <li>• <strong>全面错误分析</strong>：系统性识别所有错误类型，提供修正方案和学习建议</li>
          <li>• 实际使用时，AI会根据您的作文内容生成个性化的详细建议</li>
          <li>• 支持复制、打印等功能，方便您保存和使用改进建议</li>
        </ul>
      </div>
    </div>
  );
}
