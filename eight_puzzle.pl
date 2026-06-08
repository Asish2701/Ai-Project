% 8-puzzle solver with BFS, DFS, and A* search.
% State representation: a list of 9 integers in row-major order.
% The tile 0 represents the blank.

:- module(eight_puzzle, [
    goal_state/1,
    solvable/1,
    move/3,
    solve_bfs/3,
    solve_dfs/3,
    solve_astar/4,
    compare_strategies/1,
    compare_strategies/2,
    misplaced_tiles/2,
    manhattan_distance/2,
    gui_solution/4
]).

:- use_module(library(lists)).
:- use_module(library(http/json)).

goal_state([1,2,3,4,5,6,7,8,0]).

% --- State utilities -------------------------------------------------------

solvable(State) :-
    inversion_count(State, Count),
    0 is Count mod 2.

inversion_count(State, Count) :-
    exclude(=(0), State, Tiles),
    inversion_count(Tiles, 0, Count).

inversion_count([], Acc, Acc).
inversion_count([H|T], Acc, Count) :-
    count_smaller(H, T, Smaller),
    Acc1 is Acc + Smaller,
    inversion_count(T, Acc1, Count).

count_smaller(_, [], 0).
count_smaller(X, [Y|Ys], Count) :-
    count_smaller(X, Ys, Rest),
    (   X > Y
    ->  Count is Rest + 1
    ;   Count = Rest
    ).

index_of(0, State, Index) :-
    nth0(Index, State, 0).

swap_indices(State, I, J, NewState) :-
    nth0(I, State, VI),
    nth0(J, State, VJ),
    set_nth0(I, State, VJ, Temp),
    set_nth0(J, Temp, VI, NewState).

set_nth0(0, [_|T], X, [X|T]).
set_nth0(N, [H|T], X, [H|R]) :-
    N > 0,
    N1 is N - 1,
    set_nth0(N1, T, X, R).

move(State, Move, NextState) :-
    index_of(0, State, Blank),
    blank_move(Blank, Move, Target),
    swap_indices(State, Blank, Target, NextState).

blank_move(Index, up, Target) :- Index >= 3, Target is Index - 3.
blank_move(Index, down, Target) :- Index =< 5, Target is Index + 3.
blank_move(Index, left, Target) :- Index mod 3 =\= 0, Target is Index - 1.
blank_move(Index, right, Target) :- Index mod 3 =\= 2, Target is Index + 1.

neighbors(State, Moves) :-
    findall(move(Move, NextState), move(State, Move, NextState), Moves).

% --- Heuristics ------------------------------------------------------------

misplaced_tiles(State, Count) :-
    goal_state(Goal),
    misplaced_tiles(State, Goal, 0, Count).

misplaced_tiles([], [], Acc, Acc).
misplaced_tiles([0|Ss], [_|Gs], Acc, Count) :-
    misplaced_tiles(Ss, Gs, Acc, Count).
misplaced_tiles([S|Ss], [G|Gs], Acc, Count) :-
    S =\= 0,
    (   S =:= G
    ->  Acc1 = Acc
    ;   Acc1 is Acc + 1
    ),
    misplaced_tiles(Ss, Gs, Acc1, Count).

manhattan_distance(State, Distance) :-
    manhattan_distance(State, 0, 0, Distance).

manhattan_distance([], _, Acc, Acc).
manhattan_distance([0|Tiles], Index, Acc, Distance) :-
    NextIndex is Index + 1,
    manhattan_distance(Tiles, NextIndex, Acc, Distance).
manhattan_distance([Tile|Tiles], Index, Acc, Distance) :-
    Tile =\= 0,
    GoalIndex is Tile - 1,
    row_col(Index, Row, Col),
    row_col(GoalIndex, GoalRow, GoalCol),
    Step is abs(Row - GoalRow) + abs(Col - GoalCol),
    Acc1 is Acc + Step,
    NextIndex is Index + 1,
    manhattan_distance(Tiles, NextIndex, Acc1, Distance).

row_col(Index, Row, Col) :-
    Row is Index // 3,
    Col is Index mod 3.

% --- Search result helpers -------------------------------------------------

reconstruct_path(Node, Path) :-
    reconstruct_path_(Node, RevPath),
    reverse(RevPath, Path).

reconstruct_path_(node(State, _, _, _, none), [State]).
reconstruct_path_(node(State, _, _, _, Parent), [State|Path]) :-
    Parent \= none,
    reconstruct_path_(Parent, Path).

solution_stats(Path, Expanded, DurationMS, Stats) :-
    length(Path, Length),
    Moves is Length - 1,
    Stats = stats{moves:Moves, expanded:Expanded, runtime_ms:DurationMS}.

search_result(Path, Expanded, DurationMS, Result) :-
    solution_stats(Path, Expanded, DurationMS, Stats),
    Result = result{path:Path, stats:Stats}.

solvable_pair(Start, Goal) :-
    inversion_count(Start, C1),
    inversion_count(Goal, C2),
    0 is (C1 - C2) mod 2.

% --- BFS ------------------------------------------------------------------

solve_bfs(Start, Goal, Result) :-
    search_start(Start, Goal),
    statistics(runtime, [T0|_]),
    bfs([node(Start, 0, none, 0, none)], [Start], Goal, Node, Expanded),
    statistics(runtime, [T1|_]),
    Duration is T1 - T0,
    reconstruct_path(Node, Path),
    search_result(Path, Expanded, Duration, Result).

bfs([Node|_], _, Goal, Node, Expanded) :-
    Node = node(State, _, _, _, _),
    State == Goal,
    Expanded = 0.
bfs([Node|Rest], Visited, Goal, Solution, Expanded) :-
    Node = node(State, G, _, _, _),
    State \== Goal,
        findall(node(Next, _G1, none, 0, Node),
            ( move(State, _, Next),
              \+ memberchk(Next, Visited)
            ),
            Children),
    children_with_costs(Children, G, Node, ChildNodes),
    append(Visited, [State], Visited1),
    append(Rest, ChildNodes, Queue1),
    length(ChildNodes, Added),
    bfs(Queue1, Visited1, Goal, Solution, ExpandedRest),
    Expanded is ExpandedRest + Added + 1.

children_with_costs([], _, _, []).
children_with_costs([node(State, _, _, _, Parent)|Rest], G, Parent, [node(State, G1, none, 0, Parent)|More]) :-
    G1 is G + 1,
    children_with_costs(Rest, G, Parent, More).

% --- DFS ------------------------------------------------------------------

solve_dfs(Start, Goal, Result) :-
    search_start(Start, Goal),
    statistics(runtime, [T0|_]),
    dfs(node(Start, 0, none, 0, none), Goal, [Start], Node, Expanded),
    statistics(runtime, [T1|_]),
    Duration is T1 - T0,
    reconstruct_path(Node, Path),
    search_result(Path, Expanded, Duration, Result).

dfs(Node, Goal, _, Node, 0) :-
    Node = node(State, _, _, _, _),
    State == Goal.
dfs(Node, Goal, Visited, Solution, Expanded) :-
    Node = node(State, _, _, _, _),
    State \== Goal,
    move_order(State, NextStates),
    dfs_children(NextStates, Node, Goal, Visited, Solution, Expanded).

move_order(State, Moves) :-
    findall(Next, move(State, _, Next), Moves).

dfs_children([], _, _, _, _, 0) :- fail.
dfs_children([Next|_], Parent, Goal, Visited, Solution, Expanded) :-
    \+ memberchk(Next, Visited),
    Parent = node(_, G, _, _, _),
    G1 is G + 1,
    dfs(node(Next, G1, none, 0, Parent), Goal, [Next|Visited], ChildSolution, ChildExpanded),
    Solution = ChildSolution,
    Expanded is ChildExpanded + 1.
dfs_children([_|Rest], Parent, Goal, Visited, Solution, Expanded) :-
    dfs_children(Rest, Parent, Goal, Visited, Solution, Expanded).

% --- A* -------------------------------------------------------------------

solve_astar(Start, Goal, Heuristic, Result) :-
    search_start(Start, Goal),
    heuristic_value(Heuristic, Start, H0),
    statistics(runtime, [T0|_]),
    astar([node(Start, 0, none, H0, none)], [], Goal, Heuristic, Node, Expanded),
    statistics(runtime, [T1|_]),
    Duration is T1 - T0,
    reconstruct_path(Node, Path),
    search_result(Path, Expanded, Duration, Result).

heuristic_value(misplaced, State, Value) :- misplaced_tiles(State, Value).
heuristic_value(manhattan, State, Value) :- manhattan_distance(State, Value).

astar([Node|_], _, Goal, _, Node, 0) :-
    Node = node(State, _, _, _, _),
    State == Goal.
astar([Node|Open], Closed, Goal, Heuristic, Solution, Expanded) :-
    Node = node(State, _, _, _, _),
    memberchk(State, Closed),
    !,
    astar(Open, Closed, Goal, Heuristic, Solution, Expanded).
astar([Node|Open], Closed, Goal, Heuristic, Solution, Expanded) :-
    Node = node(State, G, _, _, _),
    State \== Goal,
    findall(Child,
            astar_child(State, G, Node, Heuristic, Closed, Open, Child),
            Children),
    insert_all_by_f(Children, Open, Open1),
    astar(Open1, [State|Closed], Goal, Heuristic, Solution, ExpandedRest),
    length(Children, Added),
    Expanded is ExpandedRest + Added + 1.

astar_child(State, G, Parent, Heuristic, Closed, _Open, node(Next, G1, none, F1, Parent)) :-
    move(State, _, Next),
    \+ memberchk(Next, Closed),
    G1 is G + 1,
    heuristic_value(Heuristic, Next, H1),
    F1 is G1 + H1.

member_in_open(State, [node(State, _, _, _, _)|_]).
member_in_open(State, [_|Rest]) :-
    member_in_open(State, Rest).

insert_all_by_f([], Open, Open).
insert_all_by_f([Node|Nodes], Open, Final) :-
    insert_by_f(Node, Open, Open1),
    insert_all_by_f(Nodes, Open1, Final).

insert_by_f(Node, [], [Node]).
insert_by_f(Node, [Head|Tail], [Node,Head|Tail]) :-
    Node = node(_, _, _, F1, _),
    Head = node(_, _, _, F2, _),
    F1 =< F2.
insert_by_f(Node, [Head|Tail], [Head|Rest]) :-
    Node = node(_, _, _, F1, _),
    Head = node(_, _, _, F2, _),
    F1 > F2,
    insert_by_f(Node, Tail, Rest).

% --- Comparison -----------------------------------------------------------

compare_strategies(Results) :-
    default_start(Start),
    compare_strategies(Start, Results).

compare_strategies(Start, comparison{start:Start, bfs:BFS, dfs:DFS, astar_misplaced:AM, astar_manhattan:AD}) :-
    goal_state(Goal),
    solve_bfs(Start, Goal, BFS),
    solve_dfs(Start, Goal, DFS),
    solve_astar(Start, Goal, misplaced, AM),
    solve_astar(Start, Goal, manhattan, AD).

default_start([1,2,3,4,5,6,0,7,8]).
default_goal([1,2,3,4,5,6,7,8,0]).

search_start(Start, Goal) :-
    solvable_pair(Start, Goal),
    !.
search_start(_, _) :-
    throw(error(domain_error(solvable_puzzle, unsolvable_state), _)).

% --- GUI helpers ---------------------------------------------------------

gui_solution(Start, Strategy, Heuristic, Payload) :-
    catch(gui_solution_(Start, Strategy, Heuristic, Payload), Error, gui_solution_error(Error, Payload)).

gui_solution_(Start, Strategy, Heuristic, Payload) :-
    goal_state(Goal),
    gui_solve_strategy(Strategy, Start, Goal, Heuristic, Result),
    Payload = json{
        ok:true,
        start:Start,
        goal:Goal,
        strategy:Strategy,
        heuristic:Heuristic,
        result:Result
    }.

gui_solve_strategy(bfs, Start, Goal, _, Result) :-
    solve_bfs(Start, Goal, Result).
gui_solve_strategy(dfs, Start, Goal, _, Result) :-
    solve_dfs(Start, Goal, Result).
gui_solve_strategy(astar, Start, Goal, Heuristic, Result) :-
    solve_astar(Start, Goal, Heuristic, Result).

gui_solution_error(error(domain_error(solvable_puzzle, unsolvable_state), _),
    json{ok:false, error:"The selected puzzle is not solvable."}).
gui_solution_error(Error, json{ok:false, error:Message}) :-
    term_string(Error, Message).
