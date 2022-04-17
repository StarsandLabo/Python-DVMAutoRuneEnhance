# Python-DVMAutoRuneEnhance

## 目次
+ 概要
+ デモ動画
+ 目的
+ 使用ライブラリ及び役割
+ フローチャート
+ 工夫・苦労した点
+ 残っている改善点
+ 得られたこと/もの  

## 概要
  
Pythonとそのライブラリを用い、ゲームの操作を自動化をする。  
主にマウス操作自動化、画像処理と文字認識を使用する。

## デモ動画

[![Automated DVM Rune Enhance](https://img.youtube.com/vi/fQdml7Xbw2A/0.jpg)](https://www.youtube.com/watch?v=fQdml7Xbw2A)

## 目的

+ これまでのPython自体の学習及び自動化関連のアウトプット  
+ 画像処理ライブラリやOCRに興味があり、使用してみたかった。
+ ゲーム内で負担になっていた作業の負担軽減

## 使用ライブラリ及び役割

|コンポーネント名|用途|
|---:|:---:|
|PyAutoGUI|マウスの自動操作|
|OpenCV|マウス操作向けの座標取得、条件判定のための画像比較|
|Pillow|画面キャプチャの取得、画像のトリミング|
|PyOCR|画像から文字情報を取得|  
  

他 numpy 等。  
  

## フローチャート

<details><summary>サイズが大きいので折りたたみ</summary>

![フローチャート](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/flowchart_2022-04-17.jpg)  

</details>

## 工夫・苦労した点

`◎,○`…効果のあった内容。◎は特にそう感じたところ。  
`▲`…期待通りに行かなかった点  
`☓`…

### 工夫  
---

+ ### a.テンプレートマッチングの過検出への対応(近い座標を判別して一つにまとめる)  
    > ◎ 処理量を1/10以下に抑えることができた  
    + はじめはそれほど意味はないかと考えていたが、後になるほどテスト時のレスポンスが短く助かった
    
    > ▲ 座標が間引かれすぎている。  
    + 運用回避可能な範囲  
    + アルゴリズムが不完全と思われるが、調査中  
    
+ ### b.OCRによって所持金を取得し、ユーザに通知するようにした。  
    > ○ 所持金を通知する仕組みを作ることができた  

    > ▲ 通知内容の妥協  
    + 思ったよりも精度が出なかった  

+ ### c.コンソール上に出力されるログの可視性への配慮(着色や体裁)  
    > ○ テストやデバッグが非常にやりやすかった  

    > ▲ 改善できるとは思うが、代わりにコードの可視性が落ちる箇所があった  

### 苦労
---

+ テンプレートマッチングの過検出を削除するアルゴリズム  
  + 最初に思いついたパターンがいつの間にかエラーがでるようになってしまったため、再度作り直した。
  + ライブラリを使えばすぐに実装できるかと思っていたが、ライブラリから意図しない戻りがあり、自作することになった。

+ 画像識別のテストに時間がかかった。  
  + どの領域を検出しているかを確認する必要があるが、座標が数値で返ってくるだけのためそれを描画してGUIで確認しなければならず、手間だった。  




### 残っている改善点
---

+ テンプレートマッチングの過検出を間引くアルゴリズム  
  + 現状下2段が間引かれているだろうという状態で、期待する品質には届いていない。  

+ OCRの精度向上  
  + 所持金の検出精度が向上できれば、書き出すファイル名に使用した金額を表すこともでき、情報としてはより有用と思う。  
  + 強化後の状態を文字でも取得することができれば、Webフレームワークなどと組み合わせて、ブラウザで結果を閲覧できるようにしたりできるかもしれない。  


### 得られたこと/もの
---

+ 自動化による手間と感じていた作業からの開放
+ 標準も含めライブラリの使い方
+ ライブラリのコードを見ることによる、他人のコードの完成度の高さに触れられた。
+ Pythonの書き方にだいぶ慣れた。
+ テストやデバッグは想像以上に手間だった
  + PowerShellのときよりもきついと感じた。

### 課題・改善したいこと
---

+ アルゴリズムの知識  
  + 今回で言えばソートや分類と行った領域？  
  
+ 不要な関数の削減  
  + 実質同じ内容なのに別関数で別れていたり、非常に再利用性の低い関数を多く作ってしまった。  
  
+ 綺麗なコーディング  
  + フローの中でいきなり関数を作り出したりしてしまった  

+ 変数の命名規則が一貫しない、似たような変数名をつけたい場面がとても多かった。

+ 有名なライブラリは使い方を少しでも抑えて効率を良くしたい
  + 今回の目的ではないけど、Pandasなどを使えばイメージする効率の良さが達成しやすくなる？