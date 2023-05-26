package org.example;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.io.OWLXMLOntologyFormat;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.owlapi.reasoner.structural.StructuralReasonerFactory;
import org.semanticweb.owlapi.util.ShortFormProvider;
import org.semanticweb.owlapi.util.SimpleShortFormProvider;

import java.io.*;
import java.util.Set;
// https://github.com/phillord/owl-api/blob/master/contract/src/test/java/org/coode/owlapi/examples/Examples.java
// Press Shift twice to open the Search Everywhere dialog and type `show whitespaces`,
// then press Enter. You can now see whitespace characters in your code.


import java.util.Collections;
import java.util.Set;

import org.coode.owlapi.manchesterowlsyntax.ManchesterOWLSyntaxEditorParser;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.expression.OWLEntityChecker;
import org.semanticweb.owlapi.expression.ParserException;
import org.semanticweb.owlapi.expression.ShortFormEntityChecker;
import org.semanticweb.owlapi.io.StringDocumentSource;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLDataFactory;
import org.semanticweb.owlapi.model.OWLEntity;
import org.semanticweb.owlapi.model.OWLNamedIndividual;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.reasoner.Node;
import org.semanticweb.owlapi.reasoner.NodeSet;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.util.BidirectionalShortFormProvider;
import org.semanticweb.owlapi.util.BidirectionalShortFormProviderAdapter;

public class Main {
    public Main() throws UnsupportedEncodingException {
    }

    public static void main(String[] args) throws OWLOntologyCreationException, IOException {

        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        File file = new File("/home/demir/Desktop/Softwares/JenaTut/family.nt");
        OWLOntology ont = manager.loadOntologyFromOntologyDocument(file);
        System.out.println("Loaded ontology: " + ont);
        System.out.println("Number of individuals: "
                + ont.getIndividualsInSignature().size());

        for (OWLNamedIndividual ind : ont.getIndividualsInSignature()) {
            System.out.println(ind);
        }
        // Create a reasoner factory. In this case, we will use HermiT,
        // but we could also use FaCT++ (http://code.google.com/p/factplusplus/)
        // or Pellet(http://clarkparsia.com/pellet)
        OWLReasoner reasoner = new StructuralReasonerFactory().createReasoner(ont, new SimpleConfiguration(new ConsoleProgressMonitor()));
        // Ask the reasoner to do all the necessary work now
        reasoner.precomputeInferences();

        // We can determine if the ontology is actually consistent (in this
        // case, it should be).
        boolean consistent = reasoner.isConsistent();
        System.out.println("Consistent: " + consistent);
        System.out.println("\n");
        // We can easily get a list of unsatisfiable classes. (A class is
        // unsatisfiable if it can't possibly have any instances). Note that the
        // getUnsatisfiableClasses method is really just a convenience method
        // for obtaining the classes that are equivalent to owl:Nothing. In our
        // case there should be just one unsatisfiable class - "mad_cow" We ask
        // the reasoner for the unsatisfiable classes, which returns the bottom
        // node in the class hierarchy (an unsatisfiable class is a subclass of
        // every class).
        Node<OWLClass> bottomNode = reasoner.getUnsatisfiableClasses();
        // This node contains owl:Nothing and all the classes that are
        // equivalent to owl:Nothing - i.e. the unsatisfiable classes. We just
        // want to print out the unsatisfiable classes excluding owl:Nothing,
        // and we can used a convenience method on the node to get these
        Set<OWLClass> unsatisfiable = bottomNode.getEntitiesMinusBottom();
        if (!unsatisfiable.isEmpty()) {
            System.out.println("The following classes are unsatisfiable: ");
            for (OWLClass cls : unsatisfiable) {
                System.out.println("    " + cls);
            }
        } else {
            System.out.println("There are no unsatisfiable classes");
        }
        System.out.println("\n");

        // Now we want to query the reasoner for all descendants of vegetarian.
        // Vegetarians are defined in the ontology to be animals that don't eat
        // animals or parts of animals.
        OWLDataFactory fac = manager.getOWLDataFactory();
        OWLClass female = fac.getOWLClass(IRI.create("http://www.benchmark.org/family#Female"));

        // Now use the reasoner to obtain the subclasses of vegetarian. We can
        // ask for the direct subclasses of vegetarian or all of the (proper)
        // subclasses of vegetarian. In this case we just want the direct ones
        // (which we specify by the "true" flag).
        NodeSet<OWLClass> subClses = reasoner.getSubClasses(female, true);
        Set<OWLClass> clses = subClses.getFlattened();
        System.out.println("Subclasses of Female: ");
        for (OWLClass cls : clses) {
            System.out.println("    " + cls);
        }
        System.out.println("\n");

        // In this case, we should find that the classes, cow, sheep and giraffe
        // are vegetarian. Note that in this ontology only the class cow had
        // been stated to be a subclass of vegetarian. The fact that sheep and
        // giraffe are subclasses of vegetarian was implicit in the ontology
        // (through other things we had said) and this illustrates why it is
        // important to use a reasoner for querying an ontology. We can easily
        // retrieve the instances of a class. In this example we'll obtain the
        // instances of the class pet. This class has a full IRI of
        // <http://owl.man.ac.uk/2005/07/sssw/people#pet> We need to obtain a
        // reference to this class so that we can ask the reasoner about it.
        // Ask the reasoner for the instances of pet
        NodeSet<OWLNamedIndividual> individualsNodeSet = reasoner.getInstances(female, true);
        // The reasoner returns a NodeSet again. This time the NodeSet contains
        // individuals. Again, we just want the individuals, so get a flattened
        // set.
        Set<OWLNamedIndividual> individuals = individualsNodeSet.getFlattened();
        System.out.println("Instances of female: ");
        for (OWLNamedIndividual ind : individuals) {
            System.out.println("    " + ind);
        }
        System.out.println("\n");
        ShortFormProvider shortFormProvider = new SimpleShortFormProvider();
        DLQueryPrinter dlQueryPrinter = new DLQueryPrinter(new DLQueryEngine(reasoner,
                shortFormProvider), shortFormProvider);
        // Enter the query loop. A user is expected to enter class
        // expression on the command line.
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        while (true) {
            System.out
                    .println("Type a class expression in Manchester Syntax and press Enter (or press x to exit):");
            String classExpression = br.readLine();
            // Check for exit condition
            if (classExpression == null || classExpression.equalsIgnoreCase("x")) {
                break;
            }
            dlQueryPrinter.askQuery(classExpression.trim());
            System.out.println();
        }
    }
    // learn manchester syntax https://ceur-ws.org/Vol-216/submission_9.pdf
    // NOT Male AND Not Son
    // hasSibling SOME Female

    }



class DLQueryEngine {
    private final OWLReasoner reasoner;
    private final DLQueryParser parser;

    public DLQueryEngine(OWLReasoner reasoner, ShortFormProvider shortFormProvider) {
        this.reasoner = reasoner;
        parser = new DLQueryParser(reasoner.getRootOntology(), shortFormProvider);
    }

    public Set<OWLClass> getSuperClasses(String classExpressionString, boolean direct) {
        if (classExpressionString.trim().length() == 0) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser
                .parseClassExpression(classExpressionString);
        NodeSet<OWLClass> superClasses = reasoner
                .getSuperClasses(classExpression, direct);
        return superClasses.getFlattened();
    }

    public Set<OWLClass> getEquivalentClasses(String classExpressionString) {
        if (classExpressionString.trim().length() == 0) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser
                .parseClassExpression(classExpressionString);
        Node<OWLClass> equivalentClasses = reasoner.getEquivalentClasses(classExpression);
        Set<OWLClass> result = null;
        if (classExpression.isAnonymous()) {
            result = equivalentClasses.getEntities();
        } else {
            result = equivalentClasses.getEntitiesMinus(classExpression.asOWLClass());
        }
        return result;
    }

    public Set<OWLClass> getSubClasses(String classExpressionString, boolean direct) {
        if (classExpressionString.trim().length() == 0) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser
                .parseClassExpression(classExpressionString);
        NodeSet<OWLClass> subClasses = reasoner.getSubClasses(classExpression, direct);
        return subClasses.getFlattened();
    }

    public Set<OWLNamedIndividual> getInstances(String classExpressionString,
                                                boolean direct) {
        if (classExpressionString.trim().length() == 0) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser
                .parseClassExpression(classExpressionString);
        NodeSet<OWLNamedIndividual> individuals = reasoner.getInstances(classExpression,
                direct);
        return individuals.getFlattened();
    }
}

class DLQueryParser {
    private final OWLOntology rootOntology;
    private final BidirectionalShortFormProvider bidiShortFormProvider;

    public DLQueryParser(OWLOntology rootOntology, ShortFormProvider shortFormProvider) {
        this.rootOntology = rootOntology;
        OWLOntologyManager manager = rootOntology.getOWLOntologyManager();
        Set<OWLOntology> importsClosure = rootOntology.getImportsClosure();
        // Create a bidirectional short form provider to do the actual mapping.
        // It will generate names using the input
        // short form provider.
        bidiShortFormProvider = new BidirectionalShortFormProviderAdapter(manager,
                importsClosure, shortFormProvider);
    }

    public OWLClassExpression parseClassExpression(String classExpressionString) {
        OWLDataFactory dataFactory = rootOntology.getOWLOntologyManager()
                .getOWLDataFactory();
        ManchesterOWLSyntaxEditorParser parser = new ManchesterOWLSyntaxEditorParser(
                dataFactory, classExpressionString);
        parser.setDefaultOntology(rootOntology);
        OWLEntityChecker entityChecker = new ShortFormEntityChecker(bidiShortFormProvider);
        parser.setOWLEntityChecker(entityChecker);
        return parser.parseClassExpression();
    }
}

class DLQueryPrinter {
    private final DLQueryEngine dlQueryEngine;
    private final ShortFormProvider shortFormProvider;

    public DLQueryPrinter(DLQueryEngine engine, ShortFormProvider shortFormProvider) {
        this.shortFormProvider = shortFormProvider;
        dlQueryEngine = engine;
    }

    public void askQuery(String classExpression) {
        if (classExpression.length() == 0) {
            System.out.println("No class expression specified");
        } else {
            try {
                StringBuilder sb = new StringBuilder();
                sb.append("\\nQUERY:   ").append(classExpression).append("\\n\\n");
                Set<OWLClass> superClasses = dlQueryEngine.getSuperClasses(
                        classExpression, false);
                printEntities("SuperClasses", superClasses, sb);
                Set<OWLClass> equivalentClasses = dlQueryEngine
                        .getEquivalentClasses(classExpression);
                printEntities("EquivalentClasses", equivalentClasses, sb);
                Set<OWLClass> subClasses = dlQueryEngine.getSubClasses(classExpression,
                        true);
                printEntities("SubClasses", subClasses, sb);
                Set<OWLNamedIndividual> individuals = dlQueryEngine.getInstances(
                        classExpression, true);
                printEntities("Instances", individuals, sb);
                System.out.println(sb.toString());
            } catch (ParserException e) {
                System.out.println(e.getMessage());
            }
        }
    }

    private void printEntities(String name, Set<? extends OWLEntity> entities,
                               StringBuilder sb) {
        sb.append(name);
        int length = 50 - name.length();
        for (int i = 0; i < length; i++) {
            sb.append(".");
        }
        sb.append("\\n\\n");
        if (!entities.isEmpty()) {
            for (OWLEntity entity : entities) {
                sb.append("\\t").append(shortFormProvider.getShortForm(entity))
                        .append("\\n");
            }
        } else {
            sb.append("\\t[NONE]\\n");
        }
        sb.append("\\n");
    }
}