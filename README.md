# Note Comparer Anki
An anki addon for 2.1 for comparing notes for duplicates.

## What to use Note Comparer for?
![Main window](/screenshots/main.jpg)
<br>The purpose of the addon is to compare notes for duplicates. You can group notes based on their deck, note type or tag(s) or select them from the browser (see the point 'Select notes from browser' below for more information). You can then compare notes between the groups by specifying fields that need to match or by entering manual conditions yourself. Notes with either matching fields or fulfilling the conditions are seen as duplicates and you can then perform separate actions on them such as delete, (un)suspend and tagging and replacing a field for another:

## Important to know
<ul>
  <li><b>You can find the program under Tools -> Note Comparer</b></li>
  <li>Please backup your notes/decks! When you make a mistake it could potentially alter/delete your notes!</li>
  <li>It can take a while to show a lot of duplicates after they have been found.</li>
</ul>

## Select notes from browser
When choosing the option 'Browser' to group notes by, the browser opens up and you can then add notes to a group by selecting them, right clicking and choosing 'Add notes to group X'. This saves the current selection of notes as 'Selection X' and automatically selects it, but you can always select it later whenever 'Browser' is selected as the first option.

## Manual conditions
![Advanced mode](/screenshots/advanced.jpg)
<br>When enabling 'Advanced mode', you can manually specificy conditions which determine whether notes from different groups are seen as duplicates.
To that end, you have to specify which (parts of) fields much match in order for the notes to be seen as duplicates (field values = fields, in this context):
<ul style='list-style-position: inside'>
  <li>
    Any field can be specified as '<code>GxFy</code>' where '<code>x</code>' and '<code>y</code>' indicate the group number and field number respectively.
    <br><b>Example</b>: '<code>G1F1</code>' means field 1 of group 1.
    <br>Instead of a field you can also specify any text by surrounding it with single quotes (f.e. <code>'example'</code>). 
  </li>
  <li>
  <div>Any pair of fields can be compared as '<code>GxFy [operator] GaFb</code>' (now referred to as a 'condition').
  Possible operators are:</div>
    <ul>
      <li>'<code>=</code>': This means that both fields must exactly match for the condition to be seen as '<code>True</code>'. Text in quotes must be on the right side.</li>
      <li>'<code>in</code>': This means that the field left from the [operator] must be present somewhere in the field to the right for the condition to be '<code>True</code>'. 
      If the left field is a single word it must also be present as a single word in the right field. Text in quotes must be on the left.</li>
      <li>'<code>></code>': This means the same as <code>in</code>, but the left field doesn't have to be present as a single word in the right field, but can also be part of a       word.</li>
      </ul>
        <div><b>Example 1</b>: '<code>G1F1 in G2F1</code>' means that field 1 of group 1 needs to be present in field 1 of group 2.</div>
        <div><b>Example 2</b>: '<code>G1F1 = 'ball'</code>' means that field 1 of group 1 match exactly match 'ball'.</div>
        <div><b>Example 3</b>: '<code>'ball' > G1F1</code>' means that the letters 'ball' need to be present in field 1 of group 1, so it can match either 'football' or                 'basketball'.</div></li>
  <li>Any number of conditions can be strung together by using:
    <ul>
      <li>'<code>and</code>': This means that the conditions left and right from '<code>and</code>' must be '<code>True</code>' for this 'group condition' to also be    
      '<code>True</code>'.</li>
      <li>'<code>or</code>': This means that one of both conditions must be 'True'.</li>
    </ul>
    <div><b>Example</b>: '<code>G1F1 = G2F1 and 'ball' in G1F2</code>' means that the first field of both groups must match
    AND that the word 'ball' must be present in field 2 of group 1. However, it is important to note that conditions are evaluated from left to right,
    so if let's say you have three conditions with the following values in succession '<code>True and False or True</code>',
    the first two conditions '<code>True and False</code>' are together <code>'False'</code> so the whole thing now reads '<code>False or True</code>'. Following that, it is then interpreted as '<code>True</code>'.</div>
  </li>
  <li>Any number of conditions can be given precedence by using parentheses.
      <br><b>Example</b>: '<code>(G1F1 = G2F1 and G1F2 = G2F2) or (G1F3 = G2F3 and G1F4 = G2F4)</code>' means that either fields 1 and 2 must match OR fields 3 and 4
      in order for all of these conditions together to be seen as '<code>True</code>' and the notes to be seen as duplicates.
  </li>
</ul>

## Regular expression capture and conditions
![Regex capture](/screenshots/regex.jpg)
<p>If 'RegEx capture' has been enabled, you will be able to specify part(s) for each field instead of the whole field 
by entering a regular expression in the 'RegEx' boxes and capturing certain parts in parenthesis.
Any captured group of a field can then be referenced in the conditions box (see the point above) as '<code>GxFyRz</code>' where '<code>z</code>' is the captured group number.
If you don't know how regular expressions work, please read about them somewhere in order to use this program's capabilities to the fullest.
<br><b>Example 1</b>: Let's say I have entered the regular expression '<code>\d{2}-\d{2}-\d{4}</code>' in order to capture the day, month and year field 1 of group 1 called 'date'.
I can then reference the day, month and year using '<code>G1F1R1</code>', '<code>G1F1R2</code>' and '<code>G1F1R3</code>' respectively.
<br><br>You can also use an regular expression in the place of a quoted text (even when this option is disabled). You just have to use a forward slash instead of quotes (f.e. <code>/regex/</code>).
When used in conjuction with the '<code>=</code>' or '<code>in</code>' operators the other field has to match the regular expression either entirely or partly respectively.
<br><b>Example 2</b>: '<code>/\d/ in G1F1 or G1F2 = /\w/</code>' means that there must be at least a single digit in field 1 or field 2 must be exactly one letter.</p>

## Replace Action
<p>When the 'Replace with...' action is selected, you can enter a replacement for the first selected field
of any notes in that group. The replacement for the first selected field can either be normal text or a reference to a field value.
This is of the form '<code>GxFy(Rz)</code>', where '<code>x</code>' is the group,
'<code>y</code>' the field and '<code>z</code>' the optional captured group (without parentheses).
<br>(Please see the points above about 'Manual conditions' and 'Regular expressions' for more information on how to construct a reference to a field value).</p>

## Actions
![Actions](/screenshots/action.jpg)<br>
After comparison you can also change the actions you want to perform on each note separately.

## Future additions
<ul>
  <li>Add an action to transfer card statistics.</li>
</ul>

## Contact
For (future) suggestions or bugs you can either make a issue here on github or contact me via my email ramonamerong@live.nl.
